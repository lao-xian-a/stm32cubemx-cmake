# STM32CubeMX AI Skill

让 AI 根据原理图或接线需求配置 STM32，再通过本机 STM32CubeMX 命令行生成官方 CMake 工程。适用于 Codex，也可供支持 Agent Skills 的其他客户端使用。

当前公开发布版本为 **v2**。本版完善了从参考代码重建配置、先验证纯框架再补应用、自定义 USB 与 USER CODE 保留的流程。许可为 MIT。

## 支持范围

| 目标 | 家族适配内容 | 通用示例 |
| --- | --- | --- |
| STM32F405 | 时钟、GPIO、ADC、DMA Stream/Channel、USB OTG FS、SWD 与 CCM 限制 | STM32F405RGT6 / LQFP64 |
| STM32F103C8T6 | 时钟、AFIO、GPIO、ADC 校准与时钟、DMA Channel、USB Device、SWD | STM32F103C8T6 / LQFP48 |

示例均以 3.3 V、8 MHz 外部晶振为条件，包含两路 ADC 扫描和循环 DMA、一个外部上拉低有效输入及 USB CDC 初始化。F405 系列的其他封装、容量和外设组合按具体型号及原理图调整。

## 两个示例是什么

示例是通用 `.ioc` 配置模板，由 CubeMX 生成初始化代码和 CMake 工程，供 AI 或使用者在具体项目中继续配置。

| 项目 | `examples/f405_demo.ioc` | `examples/f103c8_demo.ioc` |
| --- | --- | --- |
| 芯片 | STM32F405RGT6，LQFP64 | STM32F103C8T6，LQFP48 |
| 晶振与主频 | 8 MHz HSE，168 MHz SYSCLK | 8 MHz HSE，72 MHz SYSCLK |
| 模拟输入 | PA0 / PA1，ADC1 IN0 / IN1 | PA0 / PA1，ADC1 IN0 / IN1 |
| ADC 时钟 | 21 MHz | 12 MHz |
| 循环 DMA | DMA2 Stream0 Channel0 | DMA1 Channel1 |
| 示例按键 | PB0，无内部上下拉，外接上拉，按下接地 | 相同 |
| USB | PA11 / PA12，CDC 虚拟串口 | 相同 |
| 调试 | PA13 / PA14，SWD | 相同 |

示例生成后的 `main` 为初始化骨架。启动 ADC、按键消抖和 CDC 业务协议随具体应用实现。两个示例已完成 CubeMX 生成和 CMake 编译验证，逐板实物验证状态见验证记录。

## 安装技能

将本仓库内容复制到个人技能目录 `~/.codex/skills/stm32cubemx-cmake`，确保该目录直接包含 `SKILL.md`、`agents`、`references`、`scripts` 和 `examples`。在 Windows 上 `~` 表示自己的用户目录。

技能启用了自动匹配。需要显式调用时使用 `$stm32cubemx-cmake`。

示例请求如下。

```text
使用 $stm32cubemx-cmake 配置 STM32F103C8T6。
晶振为 8 MHz，PA0/PA1 接模拟电压，PB0 接已有外部上拉的低有效按键。
USB 使用 CDC，保留 SWD。生成 CMake 工程并编译。
```

## 使用生成脚本

需要 Python 3.10+、STM32CubeMX、对应 STM32Cube 固件包。编译还需要 CMake、Ninja 和 ARM GCC。脚本只依赖 Python 标准库。CubeMX 的 CMake 支持及具体输出结构取决于安装版本。

先把所需示例 `.ioc` 复制到新的工作目录，或使用自己的工程。脚本在该 `.ioc` 的父目录生成工程，调用前按照自己的版本管理流程保留已有源码和固件。

PowerShell 中设置本机路径并执行。

```powershell
$env:CUBEMX_PATH = 'C:\Tools\STM32CubeMX\STM32CubeMX.exe'
python scripts/cubemx_generate.py --ioc 'C:\Projects\Controller\Board.ioc' --build
```

也可以显式指定路径。

```text
python scripts/cubemx_generate.py --ioc /path/to/Board.ioc --cubemx /path/to/STM32CubeMX --build
```

Windows `.exe` 默认使用同目录的 `jre/bin/java.exe`，可用 `--java` 或 `CUBEMX_JAVA` 覆盖。macOS 可提供 `.app` 或其原生可执行文件。Linux/macOS 启动分支供适配使用，当前验证状态见 [VALIDATION.md](VALIDATION.md)。

`--timeout` 指定 CubeMX 超时秒数，默认 240。`--build` 调用 CMake configure/build 预设，默认 `Debug`，可用 `--preset` 更改。运行脚本会把当前工程的生成工具链设为 CMake。

本地脚本和日志位于工程的 `.cubemx-local`，其中会包含本机信息，目录已加入 `.gitignore`。日志应结合生成代码核对，进程退出码和构建成功各自代表不同阶段的结果。

## 工作流

1. 确认料号、封装、电压、晶振、接线和通信协议。
2. 查询本机 CubeMX 数据库并编辑 `.ioc`，维护引脚和外设依赖。
3. 调用 CubeMX `-q` 静默脚本模式执行 `project generate`。
4. 检查生成的引脚宏、外设初始化和时钟。
5. 编译工程，交付 `.ioc`、完整工程和验证状态。

生成的示例是初始化骨架。运行采集和通信时，需要根据应用实现 ADC 启动、F1 校准、按键消抖及 CDC 数据协议。实物验证状态在验证记录中明确标注。

## 文件

| 路径 | 内容 |
| --- | --- |
| `SKILL.md` | AI 技能入口及工作流程 |
| `agents/openai.yaml` | 技能展示与自动匹配设置 |
| `references/family-profiles.md` | F405 / F103 家族差异与官方资料 |
| `scripts/cubemx_generate.py` | 调用 CubeMX 并按需编译 |
| `examples/*.ioc` | 通用配置示例 |
| `VALIDATION.md` | 实际验证结果与范围 |
| `PRIVACY.md` | 发布包内容和隐私检查范围 |
| `SHA256SUMS` | 发布文件内容校验值 |

脚本结果检测的回归测试可通过 `python -m unittest discover -s tests -v` 运行。这些测试覆盖命令失败、生成结果缺失和完整成功三种情况。实际 CubeMX 验证结果见验证记录。

## 分享与许可

发布包使用通用示例和路径。分享自己的运行结果前，应检查 `.ioc` 中的自定义路径、日志、构建缓存、设备标识、凭证及 Git 历史。

本项目采用 [MIT License](LICENSE)。STM32CubeMX 和 STM32Cube 固件包由使用者按 ST 的许可单独安装。本仓库调用本机安装的软件，发布文件包括技能文本、自有脚本和通用 `.ioc` 示例。
