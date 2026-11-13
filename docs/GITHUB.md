# Publish to GitHub

Target account discovered for this project: **vish-go**. Suggested repository: **advisoriq**.

## If ChatGPT uploads it for you

Create https://github.com/new with the name `advisoriq`, choose visibility, and select **Add a README file** to initialize a branch. Share the repository URL in this conversation. Ensure the GitHub app has access to that repository. The connected tools can upload and commit code to an accessible repository but cannot create the repository itself.

## Push it yourself from VS Code

Extract the archive, open its `advisoriq` folder in VS Code, then open Terminal. Create an **empty** GitHub repository (without README) for this command-line route.

```bash
git init -b main
git add .
git status
```

Before committing, confirm `.env`, `.venv`, `models/` and `chroma_store/` are absent from staged files. `.env.example` is intentionally included. If Git asks for your identity, configure your own name and email or GitHub-provided private commit email.

```bash
git commit -m "Build AdvisorIQ research and transaction review copilot"
git remote add origin https://github.com/vish-go/advisoriq.git
git push -u origin main
```

VS Code/Git may open a browser for GitHub sign-in. Do not paste passwords or access tokens into chat. If `origin` already exists, inspect it with `git remote -v` before changing anything.

If you already initialized a remote README, use a fresh clone of that repository and copy the project files into the clone, including `.github/`, `.gitignore`, `.env.example` and `.dockerignore`. Exclude any local `.git` directory. Then add, commit and push normally. Do not force push to fix an unrelated-history rejection.

## After the push

1. Open the Actions tab and confirm the tests workflow passes.
2. Add repository topics: `python`, `langchain`, `gemini`, `rag`, `gradio`, `scikit-learn`, `fintech`.
3. Put a short demo video or screenshot in the README after recording it yourself; no keys or private data.
4. Deploy the no-key demo using the README's Render instructions if desired.
5. Add the public demo URL to GitHub's About section only after checking it works.
6. Use the qualified resume wording in INTERVIEW.md.
