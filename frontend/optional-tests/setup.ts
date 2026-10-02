import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";
import "@testing-library/jest-dom/vitest";

let n = 0;
URL.createObjectURL = vi.fn(() => `blob:mock-${++n}`);
URL.revokeObjectURL = vi.fn();
afterEach(cleanup);   // vitest globals are off, so Testing Library will not clean up on its own
