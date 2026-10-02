from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Conversation, Message, User
from app.schemas.auth import Language, Level, ScriptPref
from app.schemas.tutor import ConversationOut, MessageOut, TutorChatIn
from app.services import images
from app.services.ai import AIError, get_ai, get_vision_ai
from app.services.language import EARLIER_IMAGE_NOTE, build_system_prompt, resolve_profile

router = APIRouter(prefix="/api/tutor", tags=["tutor"])
HISTORY_LIMIT = 6  # recent messages sent to the model
IMAGE_ONLY_PROMPT = ("(The student sent this image without a question. Follow the rule for an image "
                     "with no question: briefly explain what it shows, then ask what they want to understand.)")


def _owned_conversation(db: Session, user: User, conv_id: int) -> Conversation:
    conv = db.get(Conversation, conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(404, "Conversation not found.")
    return conv


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.id.desc())
    return list(db.scalars(q))


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
def conversation_messages(conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _owned_conversation(db, user, conv_id).messages


@router.delete("/conversations/{conv_id}", status_code=204)
def delete_conversation(conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = _owned_conversation(db, user, conv_id)
    paths = [m.image_path for m in conv.messages if m.image_path]
    db.delete(conv)
    db.commit()
    for rel in paths:  # remove the stored images once the rows are gone
        images.delete(rel)


@router.get("/image-config")
def image_config(_: User = Depends(get_current_user)):
    """Lets the UI use the server's limits (MAX_IMAGE_MB) instead of hard-coding its own."""
    return {"max_mb": settings.max_image_mb, "types": list(images.ALLOWED)}


@router.get("/messages/{message_id}/image")
def message_image(message_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = db.get(Message, message_id)
    if not msg or not msg.image_path or msg.conversation.user_id != user.id:
        raise HTTPException(404, "Image not found.")
    path = images.resolve(msg.image_path)
    if not path or not path.is_file():
        raise HTTPException(404, "This image is no longer available.")
    return FileResponse(path, media_type=msg.image_mime or "application/octet-stream",
                        headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"})


def _history(conv: Conversation) -> tuple[list[dict], bool]:
    """Recent turns as plain text. Earlier images are marked, never re-sent. Returns (history, had_image)."""
    out, had_image = [], False
    for m in conv.messages[-HISTORY_LIMIT:]:
        content = m.content
        if m.image_path:
            had_image = True
            content = f"{content}\n[image attached]".strip()
        out.append({"role": m.role, "content": content})
    return out, had_image


async def _run_chat(db: Session, user: User, *, text: str, conversation_id: int | None, language: str,
                    level: str, script: str, image: tuple[bytes, str] | None = None) -> StreamingResponse:
    """Shared by the text-only and image endpoints: build the prompt, stream the reply, persist both turns."""
    if conversation_id:
        conv = _owned_conversation(db, user, conversation_id)
        conv.language, conv.level = language, level
    else:
        title = text[:60] if text else "Image question"
        conv = Conversation(user_id=user.id, title=title, language=language, level=level)
        db.add(conv)
        db.flush()

    prefs = user.profile
    script_pref = script if script != "auto" else prefs.preferred_script
    lang_profile, detection = resolve_profile(language, text, script_pref, prefs.last_detected_script)
    if detection.script:  # remember how this student writes
        prefs.last_detected_script = detection.script

    history, had_image = _history(conv)
    if image:
        data, mime = image
        system = build_system_prompt("image", lang_profile, level)
        user_turn = {"role": "user", "content": [
            {"type": "text", "text": text or IMAGE_ONLY_PROMPT},
            {"type": "image_url", "image_url": {"url": images.to_data_url(data, mime)}},
        ]}
        try:
            provider = get_vision_ai()
        except AIError as e:
            db.rollback()
            raise HTTPException(e.status_code, e.message)
    else:
        system = build_system_prompt("tutor", lang_profile, level, extra=EARLIER_IMAGE_NOTE if had_image else None)
        user_turn = {"role": "user", "content": text}
        provider = get_ai()

    stream = provider.stream([{"role": "system", "content": system}, *history, user_turn])
    try:  # fetch the first chunk so errors surface as a proper HTTP error, not a broken stream
        first = await anext(stream)
    except StopAsyncIteration:
        first = ""
    except AIError as e:
        db.rollback()
        raise HTTPException(e.status_code, e.message)
    if image and not first.strip():
        db.rollback()
        raise HTTPException(502, "The vision model returned no answer for this image. Please try again "
                                 "or upload a clearer image.")

    stored_path = None
    try:
        if image:
            stored_path = images.save(user.id, image[0], image[1])
        db.add(Message(conversation_id=conv.id, role="user", content=text,
                       image_path=stored_path, image_mime=image[1] if image else None))
        db.commit()
    except Exception:
        db.rollback()
        images.delete(stored_path)
        raise
    conv_id = conv.id

    async def body():
        parts = [first]
        yield first
        try:
            async for chunk in stream:
                parts.append(chunk)
                yield chunk
        except AIError as e:
            parts.append(f"\n\n[{e.message}]")
            yield f"\n\n[{e.message}]"
        finally:
            db.add(Message(conversation_id=conv_id, role="assistant", content="".join(parts)))
            db.commit()

    return StreamingResponse(body(), media_type="text/plain; charset=utf-8",
                             headers={"X-Conversation-Id": str(conv_id),
                                      "Access-Control-Expose-Headers": "X-Conversation-Id"})


@router.post("/chat")
async def chat(data: TutorChatIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return await _run_chat(db, user, text=data.message, conversation_id=data.conversation_id,
                           language=data.language, level=data.level, script=data.script)


@router.post("/chat/image")
async def chat_image(
    request: Request,
    image: UploadFile = File(...),
    message: str = Form("", max_length=4000),
    conversation_id: int | None = Form(None),
    language: Language = Form("en"),
    level: Level = Form("beginner"),
    script: ScriptPref = Form("auto"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Chat turn with an attached image (multipart). The image goes to the vision model only."""
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > images.max_bytes() + 512 * 1024:
        raise HTTPException(413, f"That image is too large. The limit is {settings.max_image_mb:g} MB.")
    data = await image.read(images.max_bytes() + 1)
    try:
        mime = images.validate(data)
    except images.ImageError as e:
        raise HTTPException(e.status_code, e.message)
    return await _run_chat(db, user, text=message.strip(), conversation_id=conversation_id,
                           language=language, level=level, script=script, image=(data, mime))
