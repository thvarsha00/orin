# Optional UI tests for image upload

Not part of your normal build (`tsc` only checks `src/`). To run them:

    npm i -D vitest@2 jsdom@25 @testing-library/react@16 @testing-library/dom @testing-library/user-event@14 @testing-library/jest-dom@6
    npx vitest run --config optional-tests/vitest.config.ts --root .

They mock `fetch`, so no backend or API key is needed. They cover: preview, remove, replace, type/size
validation, drag-and-drop, paste, sending image+question and image-only, error restore, text-only chat,
history rendering from the server, and the click-to-enlarge view.
