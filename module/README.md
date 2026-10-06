# PocketSwap

把存储空间作为低优先级后备 swap，面向小内存 Android 手机。1.0.2 起新安装默认 1024 MiB（1 GiB），分为两个 512 MiB 文件，保留至少 1024 MiB 可用存储。保持现有 zRAM、内存回收设置、CPU 频率和 SELinux 策略；没有应用保活或定位/步态模拟功能。

## 安装与状态

从 [最新正式 Release](https://github.com/rD227/pocketswap/releases/latest) 下载 `pocketswap.zip`，在 Magisk、KernelSU 或 APatch 的模块页面选择该 ZIP，正常重启，解锁主用户一次。点击模块“操作”查看状态；管理器不支持操作按钮时，使用 root 终端：

```sh
su -c 'sh /data/adb/modules/pocketswap/pocketswap.sh status'
```

`/proc/swaps` 是实际启用情况的依据。日志和状态在 `/data/adb/pocketswap/runtime.log`、`status.txt`。容量单位为 MiB；默认两个文件的可用交换容量略小于 1 GiB，因为存在交换头。

1.0.3 起状态页分别显示 `configured_disk_mib`（配置的新增磁盘容量）、`active_zram_mib`（已启用的 zRAM）和 `active_total_swap_mib`（实际总 swap）。`starting` 表示正在准备文件；`pending_resize` 表示旧文件仍有交换页，重启并解锁后会自动应用新容量。

系统设置通常显示物理 RAM，不会把后备 swap 算入 RAM。通过电脑二次确认：

```sh
adb shell "su -c 'cat /proc/swaps'"
adb shell "cat /proc/meminfo | grep -E 'MemTotal|MemAvailable|SwapTotal|SwapFree'"
adb shell "su -c 'sh /data/adb/modules/pocketswap/pocketswap.sh status'"
```

默认两个 `fallback*.swap` 表示约 1 GiB 磁盘后备 swap；旧版 2 GiB 配置则有四个文件。`SwapTotal` 还包括现有 zRAM。`Used=0` 表示已启用但暂未使用，不能据此判断未生效。`MemTotal` 仍是物理 RAM 大小。

## 更新

1.0.1 起提供 Magisk 的 `updateJson` 更新入口，位于最新正式 Release 的附件中。管理器若支持这个接口，会根据 `versionCode` 检查更新；KernelSU/APatch 及其分支的更新界面取决于管理器实现，也可以手动下载新版 ZIP 安装。

**已安装的 1.0.0 没有更新地址，须先手动安装一次 1.0.1 或更新版本。** 后续更新继续沿用 `id=pocketswap`，保留 `/data/adb/pocketswap/config.conf` 和已有交换文件。更新后正常重启、解锁生效；无需先卸载模块。

固定下载入口是 [`releases/latest/download/pocketswap.zip`](https://github.com/rD227/pocketswap/releases/latest/download/pocketswap.zip)。附件文件名固定为 `pocketswap.zip`；Release 标题与标签随版本变化。打包工具生成的 `update.json` 则指向具体标签下的 ZIP 和更新日志，避免最新下载链接与缓存的版本信息错配。首次发布新版前，尚未上传的更新附件链接不可用。

模块只使用 `service.sh`，不安装全局 `service.d` 脚本，不需要 Zygisk、LSPosed、系统目录挂载或 KernelSU 的挂载元模块。安装模块不会更新 LocationSpoofer APK。

安装器识别我们此前创建的启动脚本的精确 SHA-256，并将其备份、移出启动目录，再接管 `/data/misc_ce/0/locationspoofer_swap/fallback[0-3].swap`。文件须为 root 所有的四个 512 MiB 普通文件；不会重新初始化已存在的文件。其他同名脚本不修改，日志会提醒避免多个 swap 模块同时运行。现有交换文件不立即停用；模块将在下次启动后接管。

1.0.2 起的 1 GiB 默认值只用于新配置。升级安装保留已有 `config.conf`；若首次接管上述四文件启动脚本且没有配置文件，安装器会写入对应的 2 GiB 磁盘配置。1.0.3 起按下方“配置与容量修改”更改配置后，启动会自动协调旧文件。

## Root 与系统兼容性

| 环境 | 处理与限制 |
| --- | --- |
| Magisk | 使用官方模块安装与 late_start service 接口；本机验证环境为 Magisk 30.7、Android 11、4.19 内核。 |
| KernelSU / KernelSU Next 等分支 | 使用通用脚本模块接口；兼容管理器提供的 BusyBox 路径。不同分支需要实机验证。晚加载也可运行 service.sh，但执行时机由管理器决定。 |
| APatch | 使用通用模块接口及 APatch BusyBox 路径；尚未在 APatch 实机验证。 |
| 漏洞获得的临时 Android root | ZIP 不能凭空增加模块管理器或开机执行能力。可将完整源码解压到可信目录，以真正的 root 手动运行 `sh /可信绝对路径/pocketswap.sh start`；重启失去 root 后不会自动恢复。 |
| 虚拟空间、仅应用内 root、受限制的 UID 0 | 可能无法控制宿主内核；实际 UID、CAP_SYS_ADMIN、/proc 和 swapon 检查不通过时停止。 |
| iOS 越狱 | 不支持；这是 Android/Linux 模块。 |

安装器要求 Android 8/API 26 以上、管理器内安装、root 及可读 `/proc/swaps`。API 版本满足要求不等于内核支持。运行时还需要实际 CAP_SYS_ADMIN、允许 swap 操作的 SELinux 上下文，以及系统工具或管理器 BusyBox 提供所需命令。拒绝操作时保留日志，不自动改成 permissive，也不尝试绕过 root 管理器授权。缺少工具时会停止；原版 Android toolbox 的能力不代表所有 ROM 都一样。

1.0.3 已在 Redmi 4X、LineageOS/AOSP 11、F2FS、Magisk 实测容量调整：从四个 512 MiB 磁盘文件改为一个 512 MiB 文件；在线检查遇到交换页时显示 `pending_resize` 并保留文件，重启、首次解锁后自动清理三个多余文件。最终状态为 `active`，保留约 1536 MiB zRAM，`SwapTotal=2097144 kB`，即约 2 GiB 总 swap。源码检查共 69 项运行逻辑、17 项安装器和 7 项发布构建测试通过。KernelSU/APatch 尚未实机验证，不代表所有管理器或 ROM 均已验证。

## 文件系统和加密

**不限于 F2FS。** ext4 等文件系统也能支持 swap 文件，但需要内核启用 swap、文件系统实现支持、文件布局合适及操作权限。`fallocate` 在部分文件系统/内核上仍可能形成不适合 swap 的布局；不能只看文件系统名称。模块先用 4 MiB 小文件执行 `mkswap → swapon → swapoff`，通过后逐个创建大文件。已有文件直接尝试启用，失败保留并记录原因。某些内核可限制 swap 区域数量，过多分块也可能失败。

Btrfs 有 NOCOW 等额外要求，本模块不会替用户修改这些属性；tmpfs 等内存文件系统不适合作为磁盘后备 swap。为避免在 2 GB 手机上重现大规模写零导致的内存/I/O 压力，本版没有 `dd` 回退，也不自动创建 loop/dm-crypt 或改分区；小文件探测失败时停止，即使另一个创建方法可能可用。

FBE 手机默认使用主用户的 `/data/misc_ce/0/pocketswap`，首次解锁后启动；旧配置迁移使用上文路径。FDE 手机使用 `/data/adb/pocketswap/fde-swap`，启动完成后启用。未知/未加密存储默认拒绝，可显式设置 `ALLOW_UNENCRYPTED=1` 使用 `/data/adb/pocketswap/plain-swap`。目录为 root 700，文件为 root 600。

**这些路径和权限不构成交换数据加密保证。** fscrypt 的文件加密不能直接当作 swap 加密：部分旧内核允许启用但绕过文件加密，新内核可能直接拒绝；具有块层加密的设备还取决于实际块设备路径。真正的加密 swap 需要适当的 dm-crypt 或 loop 等独立方案，本版没有实现。`ALLOW_UNENCRYPTED` 仅控制未知/未加密存储的选址策略。交换页可能含应用敏感数据；删除文件也不等于安全擦除闪存内容。

## 配置与容量修改

**已安装模块的用户：在手机上以 root 权限编辑 `/data/adb/pocketswap/config.conf`，修改 `SIZE_MB`。** 这个数字是新增的磁盘 swap 总容量，单位为 MiB；不包含已有 zRAM，也不会改变物理 RAM。配置文件保留在模块目录之外，升级安装包会保留用户设置。

**如果目标是总 swap 2 GiB，不要直接填写 `SIZE_MB=2048`。** 例如本次 Redmi 4X 已有约 1536 MiB zRAM，设置 `SIZE_MB=512`、`CHUNK_MB=512` 才会得到约 2048 MiB 总 swap；填写 2048 会得到约 3584 MiB。其他手机先查看 `/proc/swaps` 的现有容量，再计算需要补充的磁盘容量。实际容量因交换文件头会略小。

通常只需要修改 `SIZE_MB`，保持 `CHUNK_MB=512`：

| 需要的磁盘 swap | 配置 | 512 MiB 文件数量 |
| --- | --- | --- |
| 512 MiB | `SIZE_MB=512` | 1 |
| 1 GiB（默认） | `SIZE_MB=1024` | 2 |
| 2 GiB | `SIZE_MB=2048` | 4 |
| 4 GiB | `SIZE_MB=4096` | 8 |
| 8 GiB | `SIZE_MB=8192` | 16 |

默认的 **1 GiB 磁盘 swap** 完整配置如下；需要 2 GiB 时，把第一行改为 `SIZE_MB=2048`：

```properties
SIZE_MB=1024
CHUNK_MB=512
PRIORITY=1
MIN_FREE_MB=1024
ALLOW_UNENCRYPTED=0
```

使用支持 LF 换行的 root 文件编辑器保存，整数两侧不要加空格，不要在配置项后追加注释。配置作为数据解析，不执行其中的 shell 内容。

**1.0.3 起，已有交换文件也可以直接改配置：**

1. 以 root 权限编辑 `/data/adb/pocketswap/config.conf` 的 `SIZE_MB`，保存。
2. 保持模块启用，正常重启并解锁主用户。启动时复用符合大小的文件，自动清理多余文件并重建大小不匹配的文件，不需要手动 `purge`。
3. 查看状态和 `/proc/swaps`，确认实际容量。只修改配置不会立即改变内核已经启用的 swap。

也可在解锁后手动运行 `start` 尝试应用配置：

```sh
su -c 'sh /data/adb/modules/pocketswap/pocketswap.sh start'
```

需要移除或重建的文件未使用时，可立即应用；有交换页时返回 `pending_resize`，不会主动将这些页搬回 RAM，重启解锁后再应用。检查全部待调整文件后才开始清理；遇到异常所有权或符号链接会停止。模块不会修改 zRAM 或其他模块的交换文件。

1.0.2 及更旧版本没有自动协调功能：先禁用、重启并解锁，再手动 `purge`，修改配置后启用、重启。下面的清理命令仍可用于旧版本或手动清理，须先确认文件不再使用。

手机上的 root 终端清理命令：

```sh
su -c 'sh /data/adb/modules/pocketswap/pocketswap.sh purge'
```

电脑上的 ADB 清理与检查命令：

```sh
adb shell "su -c 'sh /data/adb/modules/pocketswap/pocketswap.sh purge'"
adb shell "su -c 'cat /data/adb/pocketswap/config.conf'"
adb shell "su -c 'cat /proc/swaps'"
```

也可通过 ADB 进入手机的 root shell 修改配置。下例把新增磁盘容量改为 512 MiB，配合本机已有的约 1.5 GiB zRAM，实现约 2 GiB 总 swap：

```sh
adb shell
su
sed -i 's/^SIZE_MB=.*/SIZE_MB=512/' /data/adb/pocketswap/config.conf
cat /data/adb/pocketswap/config.conf
exit
exit
```

第一次安装且尚未创建交换文件时，可直接修改配置，再启动模块。不要手动删除仍列在 `/proc/swaps` 中的文件。

**维护模块源码的用户：** 新安装的默认值在仓库的 [`module/config.example`](module/config.example) 中。修改它后，运行 `python tools/build_release.py` 重新打包；已有用户的 `config.conf` 会被保留，需要自行按上述步骤调整容量。`module/common.sh` 中也有配置文件缺失时使用的默认值，若要修改发行版的默认容量，应同步修改其中 `ps_load_config()` 的 `SIZE_MB`，使两处一致。

下面是全部配置项及允许范围：

| 项 | 默认 | 约束 |
| --- | --- | --- |
| SIZE_MB | 1024 | 64–8192，必须能被 CHUNK_MB 整除；大容量不保证更快。 |
| CHUNK_MB | 512 | 64–512；为本机推荐保持 512。 |
| PRIORITY | 1 | 0–32757；自动调整到现有 zRAM 以下，检查实际生效值。 |
| MIN_FREE_MB | 1024 | 256–32768；每次分配均检查存储余量。 |
| ALLOW_UNENCRYPTED | 0 | 0 或 1，仅控制存储选址，见加密说明。 |

可用存储需要容纳目标容量，并留出 `MIN_FREE_MB` 的余量。例如，默认 1 GiB 配置加 1 GiB 余量，需要约 2 GiB 可用存储；2 GiB 配置则需要约 3 GiB。清理旧文件会释放其占用空间。模块不会在线覆盖、缩小或重新格式化活动交换文件。部分分块失败时保留已成功启用的文件，状态显示 `partial`；根据日志处理后可再次启动，不会因此关闭 zRAM。

不要同时运行其他更改 zRAM 优先级或接管同一交换文件的模块。zRAM 优先级在本模块启动后被其他程序改变，不会由本模块持续纠正。默认配置不是防杀进程承诺：Android LMKD 仍可能根据压力、抖动等条件终止应用，存储 swap 也比 RAM 慢，并会增加闪存写入。

## 禁用和卸载

禁用后重启生效；禁用按钮不会立即撤销活动 swap。卸载时只有确认 swap 使用量为零才执行停用，再删除本模块所有的文件。若文件里仍有交换页、主用户未解锁、或其他操作仍在执行，则保留文件和恢复脚本，避免瞬间把大量数据搬回 RAM。

卸载后如日志显示需要清理：先重启（确保模块已删除/禁用），解锁主用户，然后执行：

```sh
su -c 'sh /data/adb/pocketswap/recovery/pocketswap.sh purge'
```

清理只处理所有权标记匹配的专用目录中的预定文件，不执行 `swapoff -a`，不删除应用数据。状态、配置及小体积恢复脚本保留，便于排障；交换文件删除后这些文件不再占用 2 GB。若已有启动操作持有锁，先等它退出；重启后仍出现无效锁时，确认没有 PocketSwap 操作运行，再删除 `/data/adb/pocketswap/run.lock` 中的 pid/boot 文件与空锁目录。不要手动删除 `/proc/swaps` 中仍列出的文件。

## 许可证与构建

Copyright (C) 2026 xvsu。PocketSwap 源码按 GNU General Public License version 3（GPL-3.0-only）发布，无担保。`LICENSE` 是用户提供的完整 GNU GPL v3 文本，逐字节保留。发布 ZIP 同时包含完整模块 shell 源码、配置示例和许可证；修改后分发应遵循该许可证。

独立仓库源码位于 `module/`，旧的 `pocketswap-v1.0.0.zip` 保留为历史安装包；新版本使用下方工具生成。

使用 Python 3.10 以上构建：

```sh
python tools/build_release.py
```

产物在 `dist/`，发布时上传这四个文件：

| 文件 | 用途 |
| --- | --- |
| `pocketswap.zip` | 固定文件名的可安装模块，内容直接位于 ZIP 根目录。 |
| `update.json` | 从 `module/module.prop` 自动生成版本及下载地址。 |
| `changelog.md` | 更新界面展示的日志，来自根目录 `CHANGELOG.md`。 |
| `SHA256SUMS` | 前三个附件的 SHA-256 校验清单。 |

工具会检查模块 ID、更新入口、版本格式、标签匹配、日志包含当前版本以及许可证一致性；统一文本换行、保存 UNIX 执行权限和固定时间戳，实现同一构建环境下的重复构建。根目录 `README.md` 是打包说明的来源，直接嵌入安装 ZIP。

在 POSIX shell 环境运行源码测试（swap 操作与 root 身份均模拟，不修改设备路径）：

```sh
sh module/tests/test_common.sh module/common.sh
sh module/tests/test_installer.sh module
python -m unittest discover -s tests -v
```

## 发布新版本

1. 修改 `module/module.prop` 的 `version` 和递增的 `versionCode`；保持 `id`、`updateJson` 不变。在 `CHANGELOG.md` 中添加对应版本。
2. 运行测试和 `python tools/build_release.py --tag v1.0.3`（以实际版本替换）。`update.json` 由工具生成，不要另行手写修改。
3. 提交并推送源码，然后推送与模块版本一致的标签，例如 `v1.0.3`。仓库内的发布工作流会测试、打包，并创建包含四个附件的 **GitHub Release 草稿**；若已经存在该标签的正式 Release，则拒绝覆盖。
4. 在 GitHub 检查草稿及附件，发布为正式版本并设为 Latest。发布后验证最新入口以及 `update.json` 中的具体版本下载链接均可访问。

也可跳过工作流，在 GitHub 手动创建与版本一致的 Release，上传 `dist/` 中的四个文件。Release 名称、标签均可更新，附件名需要保持一致。不要将只有源码压缩包、缺少这四个附件的 Release 设为 Latest；GitHub 自动生成的 Source code ZIP 不能当作模块安装包。

现有 1.0.0 使用过的标签 `v1` 可保留；新的版本按 `v1.0.1` 等标签发布。关于 Latest 下载链接与更新格式，见 [GitHub 官方说明](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases) 和 [Magisk 官方说明](https://topjohnwu.github.io/Magisk/guides.html)。

参考：[Magisk 模块指南](https://topjohnwu.github.io/Magisk/guides.html)、[KernelSU 模块指南](https://kernelsu.org/guide/module.html)、[APatch 模块指南](https://apatch.dev/apm-guide.html)、[swapon 文件布局限制](https://man7.org/linux/man-pages/man8/swapon.8.html)、[Linux fscrypt 限制](https://www.kernel.org/doc/html/next/filesystems/fscrypt.html)、[Android LMKD](https://source.android.com/docs/core/perf/lmkd)。
