# Clean LaTeX Resume Template

A minimal, single-page resume template built with **LuaLaTeX**. Designed for software engineers but easily adaptable to any field.

![Preview](preview.png)

## Features

- Clean single-column layout with strong visual hierarchy
- Font Awesome 5 icons for contact links (GitHub, LinkedIn, email, phone)
- Custom `joblong` environment for consistent work experience entries
- Hyperlinked contacts and project references
- Compact spacing — fits dense content on one page without feeling cramped
- Built for **LuaLaTeX** with `fontspec` for modern font support

## Setup

This template requires **LuaLaTeX** (not pdfLaTeX). LuaLaTeX ships with every major LaTeX distribution — you just need to install one.

### Windows

1. Download and install [MiKTeX](https://miktex.org/download) (recommended) or [TeX Live](https://www.tug.org/texlive/acquire-netinstall.html)
2. During MiKTeX setup, select **"Install missing packages on the fly: Yes"** — this auto-downloads any packages you don't have
3. Open a terminal and verify the install:
   ```bash
   lualatex --version
   ```

### macOS

1. Download and install [MacTeX](https://www.tug.org/mactex/) (full TeX Live distribution for Mac, ~4 GB)
2. Verify the install:
   ```bash
   lualatex --version
   ```

Alternatively, install a smaller footprint with Homebrew:
```bash
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install fontspec fontawesome5 enumitem supertabular titlesec parskip collection-fontsrecommended
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install texlive-full
```

For a lighter install (~500 MB instead of ~5 GB):
```bash
sudo apt install texlive-base texlive-luatex texlive-latex-extra texlive-fonts-extra texlive-latex-recommended
```

Verify:
```bash
lualatex --version
```

### Overleaf (no install needed)

1. Download or clone this repo
2. Upload all files to a new Overleaf project
3. Go to **Menu → Compiler** and select **LuaLaTeX**
4. Hit Compile

---

## Building the PDF

Once LuaLaTeX is installed, compile from your terminal:

```bash
lualatex resume.tex
```

Or use any LaTeX editor with the compiler set to **LuaLaTeX**:

| Editor | How to set compiler |
|---|---|
| [TeXstudio](https://www.texstudio.org/) | Options → Build → Default Compiler → LuaLaTeX |
| [VS Code](https://code.visualstudio.com/) + [LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop) | Add `"latex-workshop.latex.tools"` config with `lualatex` (see extension docs) |
| [Overleaf](https://www.overleaf.com/) | Menu → Compiler → LuaLaTeX |

### Troubleshooting

**`fontawesome5.sty not found`** — You're missing the Font Awesome package. Install it:
```bash
# MiKTeX (auto-installs, but if needed):
mpm --install fontawesome5

# TeX Live / MacTeX:
sudo tlmgr install fontawesome5
```

**`fontspec` errors** — You're probably compiling with `pdflatex` instead of `lualatex`. Make sure your editor or command uses `lualatex`.

**Missing fonts on Linux** — Install recommended fonts:
```bash
sudo apt install fonts-lmodern
sudo tlmgr install collection-fontsrecommended
```

## Customization

### Sections

The template uses standard `\section*{}` commands. Add, remove, or reorder sections as needed.

### Work Experience

Use the `joblong` environment for each role:

```latex
\begin{joblong}{Job Title — Company Name}{Start -- End}
\item Accomplished X by doing Y, resulting in Z.
\item Another bullet point here.
\end{joblong}
```

### Projects

Projects use a simple `tabularx` layout with an optional GitHub link icon:

```latex
\begin{tabularx}{\linewidth}{@{}l r@{}}
\textbf{Project Name — Short Description (Tech Stack)} & \hfill \href{https://github.com/you/repo}{\faGithub} \\[2pt]
\multicolumn{2}{@{}X@{}}{One or two sentences describing what you built and why it matters.}\\
\end{tabularx}
```

### Contact Icons

Swap or add icons from the [Font Awesome 5 package](https://ctan.org/pkg/fontawesome5):

```latex
\href{https://yoursite.com}{\faGlobe\ yoursite.com}
```

## File Structure

```
.
├── resume.tex      # Main template — edit this
├── resume.pdf      # Compiled preview
├── preview.png     # Screenshot for the README
├── .gitignore      # Excludes LaTeX build artifacts
├── LICENSE
└── README.md
```

## License

This template is released under the [MIT License](LICENSE). Use it, fork it, make it yours.

## Contributing

Found a bug or have an improvement? PRs and issues are welcome.