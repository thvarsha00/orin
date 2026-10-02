import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type DragEvent,
} from "react";
import { useSearchParams } from "react-router-dom";
import {
  ArrowDown,
  ArrowUp,
  Code2,
  GraduationCap,
  ImagePlus,
  ListChecks,
  MessageSquare,
  Mic,
  MicOff,
  PanelLeftOpen,
  Play,
  Puzzle,
  SlidersHorizontal,
  Square,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";

import { LanguageSelect } from "../components/LanguageSelect";
import { ScriptSelect } from "../components/ScriptSelect";
import { ConversationList } from "../components/tutor/ConversationList";
import { ImageLightbox } from "../components/tutor/ImageLightbox";
import {
  AssistantMessage,
  UserMessage,
} from "../components/tutor/Message";

import { useAuth } from "../context/AuthContext";
import { exampleQuestion } from "../lib/languages";
import {
  DEFAULT_MAX_IMAGE_MB,
  formatSize,
  IMAGE_ACCEPT,
  validateImage,
} from "../lib/images";

import {
  api,
  streamTutor,
  streamTutorImage,
} from "../services/api";

import type {
  ChatMessage,
  Conversation,
  Language,
  Level,
  ScriptPref,
} from "../types";

const SUGGESTIONS = [
  {
    icon: Code2,
    label: "Explain a concept",
    prompt:
      "Explain this programming concept in simple terms: ",
  },
  {
    icon: Puzzle,
    label: "Solve step by step",
    prompt:
      "Help me solve this problem step by step, with hints first: ",
  },
  {
    icon: ListChecks,
    label: "Create a quiz",
    prompt:
      "Create a short practice quiz on this topic: ",
  },
];

const HISTORY_KEY = "orin_tutor_history_open";

interface SpeechRecognitionAlternativeLike {
  transcript: string;
}

interface SpeechRecognitionResultLike {
  isFinal: boolean;
  length: number;
  [index: number]: SpeechRecognitionAlternativeLike;
}

interface SpeechRecognitionResultListLike {
  length: number;
  [index: number]: SpeechRecognitionResultLike;
}

interface SpeechRecognitionEventLike extends Event {
  results: SpeechRecognitionResultListLike;
}

interface SpeechRecognitionErrorEventLike extends Event {
  error: string;
}

interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult:
    | ((event: SpeechRecognitionEventLike) => void)
    | null;
  onerror:
    | ((event: SpeechRecognitionErrorEventLike) => void)
    | null;
  onend: (() => void) | null;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

export default function Tutor() {
  const { user } = useAuth();

  const [lang, setLang] = useState<Language>(
    user?.profile.preferred_language ?? "en",
  );

  const [level, setLevel] = useState<Level>(
    user?.profile.skill_level ?? "beginner",
  );

  const [script, setScript] = useState<ScriptPref>(
    user?.profile.preferred_script ?? "auto",
  );

  const [convs, setConvs] = useState<Conversation[]>(
    [],
  );

  const [convId, setConvId] = useState<number | null>(
    null,
  );

  const [messages, setMessages] = useState<ChatMessage[]>(
    [],
  );

  const [input, setInput] = useState("");

  const [streaming, setStreaming] = useState(false);

  const [error, setError] = useState("");

  const [historyOpen, setHistoryOpen] = useState(() => {
    try {
      return (
        localStorage.getItem(HISTORY_KEY) !== "0"
      );
    } catch {
      return true;
    }
  });

  const [drawer, setDrawer] = useState(false);

  const [settingsOpen, setSettingsOpen] =
    useState(false);

  const [showJump, setShowJump] = useState(false);

  const [attached, setAttached] = useState<{
    file: File;
    url: string;
  } | null>(null);

  const [attachError, setAttachError] =
    useState("");

  const [maxMb, setMaxMb] = useState(
    DEFAULT_MAX_IMAGE_MB,
  );

  const [dragging, setDragging] = useState(false);

  const [previewOpen, setPreviewOpen] =
    useState(false);

  const [listening, setListening] = useState(false);

  const [voiceError, setVoiceError] =
    useState("");

  const [speakingIndex, setSpeakingIndex] =
    useState<number | null>(null);

  const [speechAvailable, setSpeechAvailable] =
    useState(true);

  const scrollRef =
    useRef<HTMLDivElement>(null);

  const stick = useRef(true);

  const taRef =
    useRef<HTMLTextAreaElement>(null);

  const abortRef =
    useRef<AbortController | null>(null);

  const fileRef =
    useRef<HTMLInputElement>(null);

  const recognitionRef =
    useRef<SpeechRecognitionLike | null>(null);

  const dragDepth = useRef(0);

  const live = useRef({
    messages: [] as ChatMessage[],
    attached:
      null as { url: string } | null,
  });

  live.current = {
    messages,
    attached,
  };

  const [params, setParams] =
    useSearchParams();

  /*
   * ------------------------------------------------------------------
   * Conversations
   * ------------------------------------------------------------------
   */

  const loadConvs = useCallback(() => {
    api<Conversation[]>("/tutor/conversations")
      .then(setConvs)
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadConvs();
  }, [loadConvs]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();

      recognitionRef.current?.abort();

      window.speechSynthesis?.cancel();

      live.current.messages.forEach(
        (message) => {
          if (message.imageUrl) {
            URL.revokeObjectURL(
              message.imageUrl,
            );
          }
        },
      );

      if (live.current.attached) {
        URL.revokeObjectURL(
          live.current.attached.url,
        );
      }
    };
  }, []);

  useEffect(() => {
    api<{ max_mb: number }>(
      "/tutor/image-config",
    )
      .then((config) =>
        setMaxMb(config.max_mb),
      )
      .catch(() => {});
  }, []);

  /*
   * ------------------------------------------------------------------
   * Speech support
   * ------------------------------------------------------------------
   */

  useEffect(() => {
    const recognitionConstructor =
      window.SpeechRecognition ??
      window.webkitSpeechRecognition;

    setSpeechAvailable(
      Boolean(
        recognitionConstructor &&
          "speechSynthesis" in window,
      ),
    );
  }, []);

  const stopSpeaking = useCallback(() => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    setSpeakingIndex(null);
  }, []);

  const speak = useCallback(
    (text: string, index: number) => {
      if (!("speechSynthesis" in window)) {
        setVoiceError(
          "Voice playback is not supported by this browser.",
        );
        return;
      }

      const cleanText = text.trim();

      if (!cleanText) {
        return;
      }

      if (
        speakingIndex === index
      ) {
        stopSpeaking();
        return;
      }

      window.speechSynthesis.cancel();

      const utterance =
        new SpeechSynthesisUtterance(
          cleanText,
        );

      /*
       * The browser uses its installed voice
       * for the selected language.
       */
      utterance.lang = String(lang);

      utterance.rate = 0.95;
      utterance.pitch = 1;
      utterance.volume = 1;

      const voices =
        window.speechSynthesis.getVoices();

      const languagePrefix =
        String(lang).toLowerCase();

      const matchingVoice =
        voices.find((voice) =>
          voice.lang
            .toLowerCase()
            .startsWith(languagePrefix),
        );

      if (matchingVoice) {
        utterance.voice =
          matchingVoice;
      }

      utterance.onstart = () => {
        setVoiceError("");
        setSpeakingIndex(index);
      };

      utterance.onend = () => {
        setSpeakingIndex(null);
      };

      utterance.onerror = () => {
        setSpeakingIndex(null);
        setVoiceError(
          "The browser could not play this response aloud.",
        );
      };

      window.speechSynthesis.speak(
        utterance,
      );
    },
    [lang, speakingIndex, stopSpeaking],
  );

  const startListening = () => {
    const Recognition =
      window.SpeechRecognition ??
      window.webkitSpeechRecognition;

    if (!Recognition) {
      setVoiceError(
        "Voice input is not supported by this browser. Try Chrome or Edge.",
      );
      return;
    }

    if (listening) {
      recognitionRef.current?.stop();
      return;
    }

    setVoiceError("");

    const recognition = new Recognition();

    recognition.lang = String(lang);

    recognition.interimResults = true;
    recognition.continuous = false;

    const startingText =
      input.trim();

    recognition.onresult = (
      event,
    ) => {
      let transcript = "";

      for (
        let i = 0;
        i < event.results.length;
        i += 1
      ) {
        const result =
          event.results[i];

        if (
          result.length > 0
        ) {
          transcript +=
            result[0].transcript;
        }
      }

      const next =
        startingText
          ? `${startingText} ${transcript}`.trim()
          : transcript.trim();

      setInput(next);
    };

    recognition.onerror = (
      event,
    ) => {
      setListening(false);

      if (
        event.error ===
        "not-allowed"
      ) {
        setVoiceError(
          "Microphone permission was blocked. Allow microphone access in your browser.",
        );
      } else if (
        event.error !==
        "aborted"
      ) {
        setVoiceError(
          "Voice input could not be started.",
        );
      }
    };

    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;

      setTimeout(() => {
        taRef.current?.focus();
      }, 0);
    };

    recognitionRef.current =
      recognition;

    try {
      recognition.start();
      setListening(true);
    } catch {
      setListening(false);
      recognitionRef.current = null;

      setVoiceError(
        "Voice input could not be started.",
      );
    }
  };

  /*
   * ------------------------------------------------------------------
   * Scrolling
   * ------------------------------------------------------------------
   */

  useEffect(() => {
    const element =
      scrollRef.current;

    if (
      element &&
      stick.current
    ) {
      element.scrollTop =
        element.scrollHeight;
    }
  }, [messages]);

  const onScroll = () => {
    const element =
      scrollRef.current;

    if (!element) {
      return;
    }

    const nearBottom =
      element.scrollHeight -
        element.scrollTop -
        element.clientHeight <
      120;

    stick.current =
      nearBottom;

    setShowJump(
      !nearBottom,
    );
  };

  const jumpToLatest = () => {
    const element =
      scrollRef.current;

    if (!element) {
      return;
    }

    stick.current = true;

    element.scrollTo({
      top: element.scrollHeight,
      behavior: "smooth",
    });
  };

  /*
   * ------------------------------------------------------------------
   * Composer
   * ------------------------------------------------------------------
   */

  useEffect(() => {
    const element =
      taRef.current;

    if (!element) {
      return;
    }

    element.style.height = "auto";

    element.style.height = `${Math.min(
      element.scrollHeight,
      176,
    )}px`;
  }, [input]);

  /*
   * ------------------------------------------------------------------
   * Conversation controls
   * ------------------------------------------------------------------
   */

  const stopCurrent = () => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
  };

  const releasePreviews = () => {
    messages.forEach(
      (message) => {
        if (message.imageUrl) {
          URL.revokeObjectURL(
            message.imageUrl,
          );
        }
      },
    );
  };

  const open = async (
    id: number,
  ) => {
    stopCurrent();
    stopSpeaking();
    releasePreviews();

    setError("");
    setVoiceError("");
    setConvId(id);
    setDrawer(false);
    stick.current = true;

    try {
      const loaded =
        await api<ChatMessage[]>(
          `/tutor/conversations/${id}/messages`,
        );

      setMessages(loaded);
    } catch (e) {
      setError(
        (e as Error).message,
      );
    }
  };

  useEffect(() => {
    const id = Number(
      params.get("c"),
    );

    if (id) {
      open(id);
      setParams(
        {},
        { replace: true },
      );
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fresh = () => {
    stopCurrent();
    stopSpeaking();
    releasePreviews();

    setConvId(null);
    setMessages([]);
    setInput("");
    setError("");
    setVoiceError("");
    setDrawer(false);

    stick.current = true;

    taRef.current?.focus();
  };

  const remove = async (
    id: number,
  ) => {
    await api(
      `/tutor/conversations/${id}`,
      "DELETE",
    ).catch(() => {});

    if (id === convId) {
      fresh();
    }

    loadConvs();
  };

  const toggleHistory = (
    next: boolean,
  ) => {
    setHistoryOpen(next);

    try {
      localStorage.setItem(
        HISTORY_KEY,
        next ? "1" : "0",
      );
    } catch {
      // Storage unavailable.
    }
  };

  /*
   * ------------------------------------------------------------------
   * Image attachment
   * ------------------------------------------------------------------
   */

  const attach = (
    files: FileList | File[] | null,
  ) => {
    const list = files
      ? Array.from(files)
      : [];

    if (!list.length) {
      return;
    }

    const problem =
      validateImage(
        list[0],
        maxMb,
      );

    if (problem) {
      setAttachError(problem);
      return;
    }

    setAttachError(
      list.length > 1
        ? "Only one image can be sent per message, so the first one was attached."
        : "",
    );

    if (attached) {
      URL.revokeObjectURL(
        attached.url,
      );
    }

    setAttached({
      file: list[0],
      url: URL.createObjectURL(
        list[0],
      ),
    });

    taRef.current?.focus();
  };

  const removeAttachment =
    () => {
      if (attached) {
        URL.revokeObjectURL(
          attached.url,
        );
      }

      setAttached(null);
      setAttachError("");
      setPreviewOpen(false);
    };

  const hasFiles = (
    event: DragEvent,
  ) =>
    Array.from(
      event.dataTransfer.types,
    ).includes("Files");

  const dragProps = {
    onDragEnter: (
      event: DragEvent,
    ) => {
      if (!hasFiles(event)) {
        return;
      }

      event.preventDefault();

      dragDepth.current += 1;
      setDragging(true);
    },

    onDragOver: (
      event: DragEvent,
    ) => {
      if (hasFiles(event)) {
        event.preventDefault();
      }
    },

    onDragLeave: (
      event: DragEvent,
    ) => {
      if (!hasFiles(event)) {
        return;
      }

      dragDepth.current -= 1;

      if (
        dragDepth.current <= 0
      ) {
        dragDepth.current = 0;
        setDragging(false);
      }
    },

    onDrop: (
      event: DragEvent,
    ) => {
      if (!hasFiles(event)) {
        return;
      }

      event.preventDefault();

      dragDepth.current = 0;
      setDragging(false);

      attach(
        event.dataTransfer.files,
      );
    },
  };

  /*
   * ------------------------------------------------------------------
   * Send message
   * ------------------------------------------------------------------
   */

  const send = async () => {
    const text =
      input.trim();

    const img = attached;

    if (
      (!text && !img) ||
      streaming
    ) {
      return;
    }

    stopSpeaking();

    setInput("");
    setError("");
    setAttachError("");
    setVoiceError("");
    setAttached(null);
    setPreviewOpen(false);
    setStreaming(true);
    setSettingsOpen(false);

    stick.current = true;

    setMessages((current) => [
      ...current,
      {
        role: "user",
        content: text,
        ...(img
          ? {
              imageUrl:
                img.url,
            }
          : {}),
      },
      {
        role: "assistant",
        content: "",
      },
    ]);

    const controller =
      new AbortController();

    abortRef.current =
      controller;

    let received = false;

    const onChunk = (
      chunk: string,
    ) => {
      received = true;

      setMessages((current) => {
        const copy = [
          ...current,
        ];

        const last =
          copy[
            copy.length - 1
          ];

        copy[
          copy.length - 1
        ] = {
          ...last,
          content:
            last.content +
            chunk,
        };

        return copy;
      });
    };

    const restore = () => {
      setMessages(
        (current) =>
          current.slice(0, -2),
      );

      setInput(text);

      if (img) {
        setAttached(img);
      }
    };

    try {
      let id: number;

      if (img) {
        const form =
          new FormData();

        form.append(
          "image",
          img.file,
        );

        form.append(
          "message",
          text,
        );

        if (convId) {
          form.append(
            "conversation_id",
            String(convId),
          );
        }

        form.append(
          "language",
          String(lang),
        );

        form.append(
          "level",
          String(level),
        );

        form.append(
          "script",
          String(script),
        );

        id =
          await streamTutorImage(
            form,
            onChunk,
            controller.signal,
            (conversationId) =>
              setConvId(
                conversationId,
              ),
          );
      } else {
        id =
          await streamTutor(
            {
              message: text,
              conversation_id:
                convId,
              language: lang,
              level,
              script,
            },
            onChunk,
            controller.signal,
            (conversationId) =>
              setConvId(
                conversationId,
              ),
          );
      }

      setConvId(id);

      loadConvs();
    } catch (e) {
      if (
        abortRef.current !==
        controller
      ) {
        return;
      }

      if (
        (e as Error).name ===
        "AbortError"
      ) {
        if (!received) {
          restore();
        }

        loadConvs();
      } else {
        restore();

        setError(
          (e as Error).message,
        );
      }
    } finally {
      if (
        abortRef.current ===
        controller
      ) {
        abortRef.current = null;
        setStreaming(false);
      }
    }
  };

  const onImageLoad = () => {
    const element =
      scrollRef.current;

    if (
      element &&
      stick.current
    ) {
      element.scrollTop =
        element.scrollHeight;
    }
  };

  const fillPrompt = (
    prompt: string,
  ) => {
    setInput(prompt);
    taRef.current?.focus();
  };

  const title =
    convs.find(
      (conversation) =>
        conversation.id ===
        convId,
    )?.title;

  /*
   * ------------------------------------------------------------------
   * Settings
   * ------------------------------------------------------------------
   */

  const controls = (
    <>
      <select
        value={level}
        onChange={(event) =>
          setLevel(
            event.target.value as Level,
          )
        }
        aria-label="Learning level"
        title="Your learning level"
        className="h-8 rounded-lg border border-line bg-white/5 px-2 text-xs outline-none focus:border-accent"
      >
        <option value="beginner">
          Beginner
        </option>

        <option value="intermediate">
          Intermediate
        </option>

        <option value="advanced">
          Advanced
        </option>
      </select>

      {lang !== "en" && (
        <ScriptSelect
          value={script}
          onChange={setScript}
          compact
        />
      )}

      <LanguageSelect
        value={lang}
        onChange={setLang}
        compact
      />
    </>
  );

  const list = (
    onCollapse?: () => void,
  ) => (
    <ConversationList
      convs={convs}
      activeId={convId}
      onOpen={open}
      onNew={fresh}
      onDelete={remove}
      onCollapse={onCollapse}
    />
  );

  /*
   * ------------------------------------------------------------------
   * UI
   * ------------------------------------------------------------------
   */

  return (
    <div
      className="absolute inset-0 flex bg-bg"
      {...dragProps}
    >
      {historyOpen && (
        <aside className="hidden w-[260px] shrink-0 border-r border-line bg-sidebar/60 lg:block">
          {list(() =>
            toggleHistory(false),
          )}
        </aside>
      )}

      <section className="relative flex min-w-0 flex-1 flex-col">
        {dragging && (
          <div className="pointer-events-none absolute inset-2 z-30 grid place-items-center rounded-2xl border-2 border-dashed border-accent/60 bg-bg/90 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-sm text-slate-200">
              <ImagePlus
                size={18}
                className="text-accent"
              />

              Drop an image to
              attach it
            </div>
          </div>
        )}

        {/* ----------------------------------------------------------
            Header
        ----------------------------------------------------------- */}

        <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-line px-3 md:px-5">
          <div className="flex min-w-0 items-center gap-2">
            {!historyOpen && (
              <button
                type="button"
                onClick={() =>
                  toggleHistory(
                    true,
                  )
                }
                aria-label="Show chats"
                title="Show chats"
                className="hidden rounded-lg p-2 text-slate-400 transition hover:bg-white/5 hover:text-white lg:inline-flex"
              >
                <PanelLeftOpen
                  size={18}
                />
              </button>
            )}

            <button
              type="button"
              onClick={() =>
                setDrawer(true)
              }
              aria-label="Open chats"
              className="rounded-lg p-2 text-slate-400 transition hover:bg-white/5 hover:text-white lg:hidden"
            >
              <MessageSquare
                size={18}
              />
            </button>

            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-accent/10 text-accent">
              <GraduationCap
                size={17}
              />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h1 className="truncate text-sm font-semibold text-white">
                  Orin Tutor
                </h1>

                {streaming && (
                  <span className="hidden items-center gap-1.5 text-[11px] text-accent sm:flex">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
                    Thinking
                  </span>
                )}
              </div>

              {title && (
                <p className="hidden max-w-[280px] truncate text-[11px] text-slate-500 sm:block">
                  {title}
                </p>
              )}
            </div>
          </div>

          <div className="hidden items-center gap-2 md:flex">
            {controls}
          </div>

          <button
            type="button"
            onClick={() =>
              setSettingsOpen(
                (open) => !open,
              )
            }
            aria-label="Tutor settings"
            aria-expanded={
              settingsOpen
            }
            className="rounded-lg p-2 text-slate-400 transition hover:bg-white/5 hover:text-white md:hidden"
          >
            <SlidersHorizontal
              size={18}
            />
          </button>

          {settingsOpen && (
            <>
              <button
                type="button"
                aria-label="Close settings"
                className="fixed inset-0 z-20 cursor-default md:hidden"
                onClick={() =>
                  setSettingsOpen(
                    false,
                  )
                }
              />

              <div className="absolute right-3 top-[52px] z-30 flex flex-col items-stretch gap-2 rounded-xl border border-line bg-panel p-3 shadow-2xl md:hidden">
                {controls}
              </div>
            </>
          )}
        </header>

        {/* ----------------------------------------------------------
            Conversation
        ----------------------------------------------------------- */}

        <div className="relative min-h-0 flex-1">
          <div
            ref={scrollRef}
            onScroll={onScroll}
            className="scroll-thin h-full overflow-y-auto"
          >
            {messages.length ===
            0 ? (
              <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col items-center justify-center px-4 py-12 text-center">
                <div className="grid h-14 w-14 place-items-center rounded-2xl bg-accent/10 text-accent ring-1 ring-accent/20">
                  <GraduationCap
                    size={27}
                  />
                </div>

                <h2 className="mt-6 text-2xl font-semibold tracking-tight text-white md:text-3xl">
                  What are you learning
                  today?
                </h2>

                <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400">
                  Ask Orin to explain a
                  concept, solve a problem,
                  review your code, or help
                  you practice.
                </p>

                <div className="mt-7 flex max-w-2xl flex-wrap justify-center gap-2">
                  {SUGGESTIONS.map(
                    ({
                      icon: Icon,
                      label,
                      prompt,
                    }) => (
                      <button
                        key={label}
                        type="button"
                        onClick={() =>
                          fillPrompt(
                            prompt,
                          )
                        }
                        className="flex items-center gap-2 rounded-xl border border-line bg-white/[0.025] px-3.5 py-2.5 text-sm text-slate-300 transition hover:border-accent/40 hover:bg-accent/10 hover:text-white"
                      >
                        <Icon
                          size={15}
                          className="text-accent"
                        />

                        {label}
                      </button>
                    ),
                  )}

                  <button
                    type="button"
                    onClick={() =>
                      fileRef.current?.click()
                    }
                    className="flex items-center gap-2 rounded-xl border border-line bg-white/[0.025] px-3.5 py-2.5 text-sm text-slate-300 transition hover:border-accent/40 hover:bg-accent/10 hover:text-white"
                  >
                    <ImagePlus
                      size={15}
                      className="text-accent"
                    />

                    Explain an image
                  </button>
                </div>

                <div className="mt-7 flex items-center gap-2 text-xs text-slate-500">
                  <span>
                    Try
                  </span>

                  <button
                    type="button"
                    onClick={() =>
                      fillPrompt(
                        exampleQuestion(
                          lang,
                          script,
                        ),
                      )
                    }
                    className="rounded text-slate-400 underline decoration-dotted underline-offset-4 transition hover:text-white"
                  >
                    {exampleQuestion(
                      lang,
                      script,
                    )}
                  </button>
                </div>
              </div>
            ) : (
              <div className="mx-auto w-full max-w-[900px] px-4 py-7 md:px-6 md:py-9">
                <div className="space-y-8">
                  {messages.map(
                    (message, index) => {
                      const isAssistant =
                        message.role ===
                        "assistant";

                      const isLast =
                        index ===
                        messages.length -
                          1;

                      return (
                        <div
                          key={index}
                          className="group"
                        >
                          {isAssistant ? (
                            <>
                              <AssistantMessage
                                message={
                                  message
                                }
                                streaming={
                                  streaming &&
                                  isLast
                                }
                              />

                              {message.content.trim() &&
                                !(
                                  streaming &&
                                  isLast
                                ) && (
                                  <div className="mt-2 ml-0 flex items-center gap-1">
                                    <button
                                      type="button"
                                      onClick={() =>
                                        speak(
                                          message.content,
                                          index,
                                        )
                                      }
                                      aria-label={
                                        speakingIndex ===
                                        index
                                          ? "Stop reading response"
                                          : "Read response aloud"
                                      }
                                      title={
                                        speakingIndex ===
                                        index
                                          ? "Stop reading"
                                          : "Read aloud"
                                      }
                                      className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[11px] text-slate-500 opacity-70 transition hover:bg-white/5 hover:text-slate-200 group-hover:opacity-100"
                                    >
                                      {speakingIndex ===
                                      index ? (
                                        <>
                                          <VolumeX
                                            size={
                                              14
                                            }
                                          />
                                          Stop
                                        </>
                                      ) : (
                                        <>
                                          <Volume2
                                            size={
                                              14
                                            }
                                          />
                                          Read aloud
                                        </>
                                      )}
                                    </button>
                                  </div>
                                )}
                            </>
                          ) : (
                            <UserMessage
                              message={
                                message
                              }
                              onImageLoad={
                                onImageLoad
                              }
                            />
                          )}
                        </div>
                      );
                    },
                  )}
                </div>
              </div>
            )}
          </div>

          {showJump && (
            <button
              type="button"
              onClick={
                jumpToLatest
              }
              aria-label="Scroll to latest message"
              title="Jump to latest"
              className="absolute bottom-4 left-1/2 grid h-9 w-9 -translate-x-1/2 place-items-center rounded-full border border-line bg-panel text-slate-300 shadow-lg transition hover:border-accent/40 hover:text-white"
            >
              <ArrowDown
                size={16}
              />
            </button>
          )}
        </div>

        {/* ----------------------------------------------------------
            Composer
        ----------------------------------------------------------- */}

        <footer className="shrink-0 px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2 md:px-6 md:pb-4">
          <div className="mx-auto w-full max-w-[900px]">
            {error && (
              <div
                role="alert"
                className="mb-2 flex items-center justify-between gap-3 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-300"
              >
                <span>
                  {error}
                </span>

                <button
                  type="button"
                  onClick={send}
                  className="shrink-0 rounded-md px-2 py-1 text-xs font-medium hover:bg-red-500/10"
                >
                  Retry
                </button>
              </div>
            )}

            {(attachError ||
              voiceError) && (
              <div
                role="alert"
                className="mb-2 flex items-center justify-between gap-3 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-sm text-amber-200"
              >
                <span>
                  {attachError ||
                    voiceError}
                </span>

                <button
                  type="button"
                  onClick={() => {
                    setAttachError(
                      "",
                    );
                    setVoiceError(
                      "",
                    );
                  }}
                  aria-label="Dismiss"
                  className="shrink-0 rounded-md p-1 hover:bg-amber-500/10"
                >
                  <X
                    size={14}
                  />
                </button>
              </div>
            )}

            <input
              ref={fileRef}
              type="file"
              accept={IMAGE_ACCEPT}
              className="hidden"
              aria-label="Choose an image"
              onChange={(event) => {
                attach(
                  event.target.files,
                );

                event.target.value =
                  "";
              }}
            />

            <div className="overflow-hidden rounded-2xl border border-line bg-[#0f1526] shadow-lg shadow-black/20 transition focus-within:border-accent/50">
              {attached && (
                <div className="flex items-center gap-3 border-b border-line p-2.5">
                  <button
                    type="button"
                    onClick={() =>
                      setPreviewOpen(
                        true,
                      )
                    }
                    aria-label="View attached image larger"
                    className="shrink-0 overflow-hidden rounded-lg border border-line bg-black/20 transition hover:border-accent/50"
                  >
                    <img
                      src={
                        attached.url
                      }
                      alt="Attached image preview"
                      className="h-14 w-14 object-contain"
                    />
                  </button>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm text-slate-200">
                      {
                        attached
                          .file
                          .name
                      }
                    </p>

                    <p className="text-xs text-slate-500">
                      {formatSize(
                        attached.file
                          .size,
                      )}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() =>
                      fileRef.current?.click()
                    }
                    className="rounded-md px-2 py-1 text-xs text-slate-400 transition hover:bg-white/5 hover:text-white"
                  >
                    Replace
                  </button>

                  <button
                    type="button"
                    onClick={
                      removeAttachment
                    }
                    aria-label="Remove image"
                    title="Remove image"
                    className="grid h-7 w-7 place-items-center rounded-full text-slate-400 transition hover:bg-white/10 hover:text-white"
                  >
                    <X
                      size={15}
                    />
                  </button>
                </div>
              )}

              <div className="flex items-end gap-1.5 p-2">
                <button
                  type="button"
                  onClick={() =>
                    fileRef.current?.click()
                  }
                  disabled={
                    streaming
                  }
                  aria-label="Attach an image"
                  title={`Attach an image (JPG, PNG or WEBP, up to ${Number(
                    maxMb.toFixed(
                      1,
                    ),
                  )} MB)`}
                  className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-40 ${
                    attached
                      ? "text-accent"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  <ImagePlus
                    size={18}
                  />
                </button>

                <button
                  type="button"
                  onClick={
                    startListening
                  }
                  disabled={
                    streaming ||
                    !speechAvailable
                  }
                  aria-label={
                    listening
                      ? "Stop voice input"
                      : "Start voice input"
                  }
                  title={
                    listening
                      ? "Stop voice input"
                      : "Voice input"
                  }
                  className={`relative grid h-9 w-9 shrink-0 place-items-center rounded-xl transition disabled:cursor-not-allowed disabled:opacity-40 ${
                    listening
                      ? "bg-accent/15 text-accent"
                      : "text-slate-400 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  {listening ? (
                    <>
                      <MicOff
                        size={18}
                      />

                      <span className="absolute -right-0.5 -top-0.5 h-2 w-2 animate-pulse rounded-full bg-accent" />
                    </>
                  ) : (
                    <Mic
                      size={18}
                    />
                  )}
                </button>

                <textarea
                  ref={taRef}
                  value={input}
                  rows={1}
                  onChange={(event) =>
                    setInput(
                      event.target
                        .value,
                    )
                  }
                  onKeyDown={(
                    event,
                  ) => {
                    if (
                      event.key ===
                        "Enter" &&
                      !event.shiftKey &&
                      !event.nativeEvent
                        .isComposing
                    ) {
                      event.preventDefault();
                      send();
                    }
                  }}
                  onPaste={(event) => {
                    const pasted =
                      Array.from(
                        event
                          .clipboardData
                          .files,
                      ).find(
                        (file) =>
                          file.type.startsWith(
                            "image/",
                          ),
                      );

                    if (pasted) {
                      event.preventDefault();
                      attach([
                        pasted,
                      ]);
                    }
                  }}
                  placeholder={
                    attached
                      ? "Ask about this image..."
                      : listening
                        ? "Listening..."
                        : "Ask Orin anything..."
                  }
                  aria-label="Message"
                  className="scroll-thin max-h-44 min-h-[36px] flex-1 resize-none bg-transparent px-1.5 py-1.5 text-[15px] leading-6 text-slate-100 outline-none placeholder:text-slate-500"
                />

                {streaming ? (
                  <button
                    type="button"
                    onClick={() =>
                      stopCurrent()
                    }
                    aria-label="Stop generating"
                    title="Stop generating"
                    className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white/10 text-white transition hover:bg-white/20"
                  >
                    <Square
                      size={14}
                      fill="currentColor"
                    />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={send}
                    disabled={
                      !input.trim() &&
                      !attached
                    }
                    aria-label="Send message"
                    title="Send message"
                    className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-accent text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <ArrowUp
                      size={18}
                    />
                  </button>
                )}
              </div>
            </div>

            <div className="mt-2 flex items-center justify-center gap-3 text-[11px] text-slate-500">
              <span>
                Learn in your
                preferred language
              </span>

              <span className="text-slate-700">
                •
              </span>

              <span>
                {speechAvailable
                  ? "Voice enabled"
                  : "Voice unavailable"}
              </span>

              <span className="text-slate-700">
                •
              </span>

              <span>
                AI responses may
                need verification
              </span>
            </div>
          </div>
        </footer>
      </section>

      {/* ------------------------------------------------------------
          Image preview
      ------------------------------------------------------------- */}

      {previewOpen &&
        attached && (
          <ImageLightbox
            src={attached.url}
            onClose={() =>
              setPreviewOpen(
                false,
              )
            }
          />
        )}

      {/* ------------------------------------------------------------
          Mobile chat history
      ------------------------------------------------------------- */}

      {drawer && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Chats"
        >
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() =>
              setDrawer(false)
            }
          />

          <aside className="absolute inset-y-0 left-0 w-72 max-w-[85vw] border-r border-line bg-sidebar shadow-2xl">
            {list()}
          </aside>
        </div>
      )}
    </div>
  );
}