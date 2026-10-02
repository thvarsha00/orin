import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Tutor from "../src/pages/Tutor";

let profile = { display_name: "V", preferred_language: "te", skill_level: "beginner", preferred_script: "auto" };
vi.mock("../src/context/AuthContext", () => ({ useAuth: () => ({ user: { id: 1, email: "a@b.c", profile } }) }));

const png = (name = "q.png", size = 2000, type = "image/png") => new File([new Uint8Array(size)], name, { type });
const enc = new TextEncoder();
const streamRes = (...chunks: string[]) => new Response(new ReadableStream({
  start(c) { chunks.forEach((x) => c.enqueue(enc.encode(x))); c.close(); },
}), { headers: { "X-Conversation-Id": "7" } });
const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "Content-Type": "application/json" } });

let calls: { url: string; init?: RequestInit }[] = [];
let chat: (url: string, init?: RequestInit) => Response;
let convs: unknown[] = [];
let history: unknown[] = [];

beforeEach(() => {
  calls = []; convs = []; history = [];
  profile = { display_name: "V", preferred_language: "te", skill_level: "beginner", preferred_script: "auto" };
  chat = () => streamRes("Here is ", "the explanation.");
  localStorage.setItem("orin_token", "tok123");
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input); calls.push({ url, init });
    if (url === "/api/tutor/conversations") return json(convs);
    if (url === "/api/tutor/image-config") return json({ max_mb: 1, types: [] });
    if (/\/messages$/.test(url)) return json(history);
    if (/\/messages\/\d+\/image$/.test(url)) return new Response(new Blob([new Uint8Array(4)], { type: "image/png" }));
    return chat(url, init);
  }));
});

const setup = () => { const user = userEvent.setup({ applyAccept: false }); render(<MemoryRouter><Tutor /></MemoryRouter>); return user; };
const fileInput = () => screen.getByLabelText("Choose an image") as HTMLInputElement;
const send = () => screen.getByLabelText("Send message") as HTMLButtonElement;
const chatCall = () => calls.find((c) => c.url.startsWith("/api/tutor/chat"))!;
const lastForm = () => chatCall().init!.body as FormData;

describe("image composer", () => {
  it("shows a preview after picking an image and enables send without any text", async () => {
    const user = setup();
    expect(send()).toBeDisabled();
    await user.upload(fileInput(), png("diagram.png", 3 * 1024));
    expect(await screen.findByAltText("Attached image preview")).toBeInTheDocument();
    expect(screen.getByText("diagram.png")).toBeInTheDocument();
    expect(screen.getByText("3 KB")).toBeInTheDocument();
    expect(send()).toBeEnabled();
  });

  it("removes and replaces the attachment", async () => {
    const user = setup();
    await user.upload(fileInput(), png("one.png"));
    await user.upload(fileInput(), png("two.jpg", 500, "image/jpeg"));
    expect(screen.queryByText("one.png")).not.toBeInTheDocument();
    expect(screen.getByText("two.jpg")).toBeInTheDocument();
    await user.click(screen.getByLabelText("Remove image"));
    expect(screen.queryByAltText("Attached image preview")).not.toBeInTheDocument();
    expect(send()).toBeDisabled();
  });

  it("rejects unsupported types and oversize files (server limit 1 MB) with clear messages", async () => {
    const user = setup();
    await waitFor(() => expect(calls.some((c) => c.url.endsWith("image-config"))).toBe(true));
    await user.upload(fileInput(), png("anim.gif", 100, "image/gif"));
    expect(await screen.findByText("Unsupported file. Please upload a JPG, PNG or WEBP image.")).toBeInTheDocument();
    expect(screen.queryByAltText("Attached image preview")).not.toBeInTheDocument();
    await user.upload(fileInput(), png("big.png", 2 * 1024 * 1024));
    expect(await screen.findByText("That image is too large. The limit is 1 MB.")).toBeInTheDocument();
    expect(screen.queryByAltText("Attached image preview")).not.toBeInTheDocument();
  });

  it("keeps the current attachment when a replacement is invalid", async () => {
    const user = setup();
    await user.upload(fileInput(), png("keep.png"));
    await user.upload(fileInput(), png("doc.pdf", 100, "application/pdf"));
    expect(screen.getByText("keep.png")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Unsupported file");
  });

  it("accepts drag-and-drop and shows the drop overlay while dragging", async () => {
    setup();
    const zone = screen.getByLabelText("Message").closest("section")!;
    const dt = { types: ["Files"], files: [png("dropped.webp", 800, "image/webp")] };
    fireEvent.dragEnter(zone, { dataTransfer: dt });
    expect(screen.getByText("Drop an image to attach it")).toBeInTheDocument();
    fireEvent.drop(zone, { dataTransfer: dt });
    expect(await screen.findByText("dropped.webp")).toBeInTheDocument();
    expect(screen.queryByText("Drop an image to attach it")).not.toBeInTheDocument();
  });

  it("accepts a pasted screenshot", async () => {
    setup();
    fireEvent.paste(screen.getByLabelText("Message"), { clipboardData: { files: [png("shot.png")] } });
    expect(await screen.findByText("shot.png")).toBeInTheDocument();
  });
});

describe("sending", () => {
  it("sends image + question as multipart with language/script/level, and renders the bubble", async () => {
    profile = { ...profile, preferred_language: "hi", preferred_script: "native" };
    const user = setup();
    await user.upload(fileInput(), png("math.png"));
    await user.type(screen.getByLabelText("Message"), "Ye sawal solve karo");
    await user.click(send());

    await screen.findByText("Here is the explanation.");
    expect(chatCall().url).toBe("/api/tutor/chat/image");
    const h = chatCall().init!.headers as Record<string, string>;
    expect(h.Authorization).toBe("Bearer tok123");
    expect(h["Content-Type"]).toBeUndefined();                 // browser must set the multipart boundary
    const f = lastForm();
    expect((f.get("image") as File).name).toBe("math.png");
    expect(f.get("message")).toBe("Ye sawal solve karo");
    expect([f.get("language"), f.get("script"), f.get("level")]).toEqual(["hi", "native", "beginner"]);
    expect(f.get("conversation_id")).toBeNull();

    const img = screen.getByAltText("Image attached by the student");
    expect(img).toHaveAttribute("src", expect.stringMatching(/^blob:/));
    expect(screen.getByText("Ye sawal solve karo")).toBeInTheDocument();
    expect(screen.queryByAltText("Attached image preview")).not.toBeInTheDocument();   // composer cleared
    expect(document.body.textContent).not.toMatch(/base64|blob:/);
  });

  it("sends an image-only message", async () => {
    const user = setup();
    await user.upload(fileInput(), png());
    await user.click(send());
    await screen.findByText("Here is the explanation.");
    expect(lastForm().get("message")).toBe("");
    expect(screen.getByAltText("Image attached by the student")).toBeInTheDocument();
  });

  it("follow-up in the same conversation reuses the conversation id", async () => {
    const user = setup();
    await user.upload(fileInput(), png());
    await user.click(send());
    await screen.findByText("Here is the explanation.");
    await user.type(screen.getByLabelText("Message"), "why?");
    await user.click(send());
    await waitFor(() => expect(calls.filter((c) => c.url === "/api/tutor/chat")).toHaveLength(1));
    expect(JSON.parse(calls.find((c) => c.url === "/api/tutor/chat")!.init!.body as string)).toMatchObject({ message: "why?", conversation_id: 7 });
  });

  it("text-only chat still goes to the JSON endpoint with no image", async () => {
    const user = setup();
    await user.type(screen.getByLabelText("Message"), "what is a tuple");
    await user.click(send());
    await screen.findByText("Here is the explanation.");
    expect(chatCall().url).toBe("/api/tutor/chat");
    expect(JSON.parse(chatCall().init!.body as string)).toMatchObject({ message: "what is a tuple", language: "te", conversation_id: null });
    expect(screen.queryByAltText("Image attached by the student")).not.toBeInTheDocument();
  });

  it("on a server error restores the text AND the image and shows the message", async () => {
    chat = () => json({ error: "Image questions need a vision model. Set GROQ_VISION_MODEL in backend/.env and restart the backend." }, 503);
    const user = setup();
    await user.upload(fileInput(), png("keep.png"));
    await user.type(screen.getByLabelText("Message"), "explain");
    await user.click(send());
    expect(await screen.findByText(/Set GROQ_VISION_MODEL/)).toBeInTheDocument();
    expect(screen.getByLabelText("Message")).toHaveValue("explain");
    expect(screen.getByText("keep.png")).toBeInTheDocument();
    expect(screen.queryByAltText("Image attached by the student")).not.toBeInTheDocument();
  });
});

describe("history + lightbox", () => {
  it("renders saved image messages from the server with auth, text below, and opens a lightbox", async () => {
    convs = [{ id: 5, title: "Old chat", language: "te", level: "beginner", created_at: "2026-01-01T00:00:00" }];
    history = [
      { id: 11, role: "user", content: "Explain this", has_image: true },
      { id: 12, role: "assistant", content: "Sure, here it is.", has_image: false },
      { id: 13, role: "user", content: "and this?", has_image: false },
    ];
    const user = setup();
    await user.click(await screen.findByText("Old chat"));
    const img = await screen.findByAltText("Image attached by the student");
    const imgCall = calls.find((c) => c.url === "/api/tutor/messages/11/image")!;
    expect((imgCall.init!.headers as Record<string, string>).Authorization).toBe("Bearer tok123");
    expect(img).toHaveAttribute("src", expect.stringMatching(/^blob:/));
    expect(screen.getByText("Explain this")).toBeInTheDocument();
    expect(screen.getAllByAltText("Image attached by the student")).toHaveLength(1);   // only the message that had one

    await user.click(screen.getByLabelText("View image larger"));
    const dlg = screen.getByRole("dialog", { name: "Image preview" });
    expect(within(dlg).getByAltText("Attached image, enlarged")).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog", { name: "Image preview" })).not.toBeInTheDocument();
  });

  it("shows a friendly placeholder if a saved image is gone", async () => {
    convs = [{ id: 5, title: "Old chat", language: "te", level: "beginner", created_at: "2026-01-01T00:00:00" }];
    history = [{ id: 21, role: "user", content: "hi", has_image: true }];
    const base = globalThis.fetch as ReturnType<typeof vi.fn>;
    vi.stubGlobal("fetch", vi.fn(async (i: RequestInfo | URL, init?: RequestInit) =>
      /\/messages\/\d+\/image$/.test(String(i)) ? json({ error: "This image is no longer available." }, 404) : base(i, init)));
    const user = setup();
    await user.click(await screen.findByText("Old chat"));
    expect(await screen.findByText("Image unavailable")).toBeInTheDocument();
    expect(screen.getByText("hi")).toBeInTheDocument();
  });
});
