# scnu-cs-thesis

scnu-cs-thesis旨在提供规范的华南师范大学计算机科学与软件工程的硕士与博士论文的 LATEX 写作模板环境，根据华南师范大学研究生学位论文撰规范 2024 版本修订。

本项目参考了 [SCNUThesis](https://github.com/scnu/scnuthesis) 项目，并根据最新的规范进行了修改。

## 近期更新

2025/5/21
1. 修改声明页日期
2. 修改答辩合格页格式和日期
3. 删除目录之前的页码

2025/5/9
1. 英文封面 Thesis -> Dissertation
2. 空白页加页码
3. 攻读硕士学位期间取得的研究成果

205/4/27
1. 2.5em -> 2em
2. 添加statement页以及相应cls
3. 作者攻读**硕士**学位期间发表的学术论文目录
4. 更换学术成果格式resume.tex
5. 证明页导师位置留空用于签名
6. 小修小补忘记了

## 变量设置

### 学位类型

在 `thesis.tex` 文件中通过 `documentclass` 设置。

例如，硕士学位论文：

```latex
\documentclass[master,vista,ttf,twoside]{scnuthesis}
```

博士学位论文：

```latex
\documentclass[doctor,vista,ttf,twoside]{scnuthesis}
```

### 基本信息

基本信息用于生成封面、摘要等包含作者、导师等信息的页面。在 `data/info.tex` 文件中填写。

### 答辩合格证明

答辩合格证明中需要填写答辩委员会成员，在 `data/committee.tex` 文件中填写。

## 使用说明

在 `myscnu.sty` 中添加你写论文需要的包。

在 `data/abstract.tex` 中撰写摘要。

在 `data/chap01.tex` 中撰写第一章内容，其余章节类似。

在 `data/appendix.tex` 中撰写附录内容。

其余内容类似，请参考 `thesis.tex` 文件。

在写完所有内容之后，在项目根目录下执行下面的命令：

```bash
xelatex thesis.tex
```

安装 `xelatex` 的方法参考下一节。

也可以使用 

https://texpage.com

https://www.overleaf.com

等在线编辑器编译。

## 高级用法

### 前置准备

首先确保你的电脑中已经安装了 `xelatex` 这个可执行文件，`macOS`可以使用下面命令安装：

```bash
brew install --cask mactex
```

该命令会将与 `texlive` 相关的可执行文件安装到 `/usr/local/texlive/${VERSION}/bin/universal-darwin` 目录下，用下面命令将该目录添加到 `$PATH` 环境变量中，即可使用 `xelatex` 命令：

```bash
export PATH=/usr/local/texlive/${VERSION}/bin/universal-darwin:$PATH
```

这里的 `${VERSION}` 是 `texlive` 的版本号，如 `2024` 等，在安装`mactex`时会有提示。

其它系统请自行搜索如何安装 `xelatex`。

### 编译步骤

本项目的完整编译过程如下，首先将 `scnuthesis.dtx` 中的内容改成你希望的格式，然后执行下面的命令：

```bash
xelatex scnuthesis.dtx
```

该命令会在项目的根目录下生成 `scnuthesis.ins` 文件，然后执行下面的命令：

```bash
xelatex scnuthesis.ins
```

该命令会在项目的根目录下生成 `scnuthesis.cls` 和 `thesis.tex` 文件，然后执行下面的命令：

```bash
xelatex thesis.tex
```

该命令会在项目的根目录下生成 `thesis.pdf` 文件，即为最终的论文。

### 更多详细配置

请参考 `scnuthesis.pdf` 文件。


## Overleaf 适配

### 使用步骤
1. Menu -> Compiler 选择 XeLatex;
2. 编译！（模板编译时间大约为5s）

### 修改内容
为契合Overleaf修改内容如下：

1. 重命名若干函数防止变量冲突；
2. 使用本地字体，可选择使用overleaf自带的开源字体；
3. 将一些临时文件归档到scnu-cs-thesis-master;
4. 其他bugs。
