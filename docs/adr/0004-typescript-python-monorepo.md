# Use a TypeScript and Python monorepo with a generated API client

Next.js supplies the interface while Python owns the API and scientific computation, allowing research code to use the Python ecosystem independently of the UI. pnpm and uv manage their respective workspaces, with Turborepo coordinating commands; a TypeScript client generated from the Python-defined API contract reduces duplicated interface definitions. This accepts two language toolchains in exchange for retaining the preferred frontend stack and independently reusable scientific packages.
