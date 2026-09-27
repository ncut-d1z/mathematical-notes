# LaTeX 编译与 PDF 发布

入口为仓库根目录的 `math.tex`。工作流从根目录编译整本书，
不修改正文、不跳过章节，也不向源码分支提交生成的 PDF。

## 构建环境

使用 `xu-cheng/latex-action@v4` 的完整 Debian TeX Live 2025 镜像。
XeLaTeX 负责中文与字体；`latexmk` 自动运行 Biber，并按参考文献、
目录和交叉引用的需要重复运行 XeLaTeX。

完整发行版提供 CTEX、Fandol 字体、`biblatex-gb7714-2015` 及其他宏包；
仓库根目录的自定义 `.sty` 直接从源码读取，不按系统宏包安装。
不再扫描宏包名后混用 `apt` / `tlmgr`，也不在每次构建时更新 TeX Live。
固定年份并非镜像摘要锁定；需要字节级固定环境时，应另行锁定镜像摘要。

编译前清理本入口的旧产物；任何 XeLaTeX/Biber/latexmk 错误都会导致失败。
不使用 `-f` 或 `|| true` 把编译错误转换为成功。
编译成功后检查非空 PDF、PDF 文件头及参考文献产物，并生成 SHA-256 校验文件。
日志中的排版警告不等于编译错误；数学内容、版面及尚未解析的引用仍需人工审核。

## 触发与产物

| 触发方式 | 编译 | 上传 Actions 产物 | 发布 Release |
| --- | --- | --- | --- |
| PR 目标为 `main` / `master` | 是 | 是 | 否 |
| 推送到 `main` / `master` | 是 | 是 | 否 |
| 推送 `v*` 标签 | 是 | 是 | 构建成功后发布 |
| 手动运行普通分支 | 是 | 是 | 否 |
| 手动运行 `v*` 标签 | 是 | 是 | 构建成功后发布 |

`compiled-pdf` 包含 `math.pdf` 和 `math.pdf.sha256`，保留 30 天。
日志产物 `latex-logs-<运行尝试号>` 保留 14 天；编译失败时也尝试保存日志。
发布 job 按本次构建的 artifact ID 下载 PDF，并核验 SHA-256，
不会误用其他运行或其他分支的 PDF。

仅发布 job 具有 `contents: write` 权限；编译 job 只有只读权限，
关闭持久化 checkout 凭据且不启用 shell escape。
发布 job 不 checkout 或编译 PR 源码。
不需要额外配置个人访问令牌，也不需要 `packages: write` 或 `issues: write`。

## 操作流程

先人工审核 PR，合并到主分支并确认整本书的构建成功。
仅需下载 PDF 时，打开对应 Actions 运行页面的 Artifacts，下载 `compiled-pdf` 即可。

需要正式发布时，在已审核的主分支提交上创建一个尚未使用的 `v*` 标签并推送。
例如，确认 `v2026.09.27` 尚不存在后，在本地运行：

```sh
git switch master
git pull --ff-only
git tag -a v2026.09.27 -m "数学笔记 PDF"
git push origin v2026.09.27
```

标签必须包含本次工作流修复；给旧提交打标签仍会执行旧版工作流。
推送成功后，新运行先构建，再在相同标签的 GitHub Release 中附加 PDF 和校验文件。
普通分支的手动构建可在 Actions → Build and Release LaTeX PDF → Run workflow 中启动。
`workflow_dispatch` 入口需要先存在于默认分支；也可以使用 GitHub CLI 指定标签运行：

```sh
gh workflow run latex.yml --repo ncut-d1z/mathematical-notes --ref v2026.09.27
```

这条手动命令同样可能发布 Release，而不只是构建。
已发布且开启不可变发布的版本不能覆盖附件；更新文档时请创建新标签。
本工作流不会自动合并 PR，也不会自动创建版本标签。

## 没有运行记录或构建失败时

这是一个 fork 仓库。首次使用时，检查仓库 Actions 页面是否需要手动启用工作流，
以及仓库/组织的 Actions 策略是否允许上面使用的 Actions。
来自 fork 的 PR 还可能需要维护者批准运行。
工作流 YAML 不能替代仓库设置中的启用操作或人工批准。

如果编译失败，查看失败步骤及 `latex-logs-*` 中的 `math.log` / `math.blg`。
全文源码自身的错误需要另行修复；不能仅凭存在一个 PDF 就认定构建成功。
Release 的权限问题应检查仓库/组织策略是否允许该 job 的 `contents: write`。

参考：
- https://github.com/xu-cheng/latex-action
- https://github.com/actions/upload-artifact
- https://github.com/actions/download-artifact
- https://github.com/softprops/action-gh-release
- https://docs.github.com/en/actions/managing-workflow-runs/manually-running-a-workflow
