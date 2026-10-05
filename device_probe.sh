#!/system/bin/sh
# Small native test; never touches the user's existing swap files or zRAM.
MOD=/data/local/tmp/pocketswap-check-20261005
for script in "$MOD"/*.sh "$MOD"/META-INF/com/google/android/update-binary; do
    /system/bin/sh -n "$script" || exit 1
done
. "$MOD/common.sh" || exit 1
PS_MODDIR="$MOD"
PS_STATE="$MOD/probe-state"
PS_PROC=/proc PS_SWAPS=/proc/swaps
PS_CE_BASE=/data/misc_ce/0/pocketswap_validation_20261005
PS_LEGACY_BASE=/data/misc_ce/0/locationspoofer_swap
ps_find_busybox
ps_root || exit 1
[ ! -e "$PS_CE_BASE" ] || { echo 'Existing test path: refusing to overwrite.'; exit 1; }
ps_tool mkdir -p "$PS_STATE" || exit 1
ps_tool chmod 700 "$PS_STATE"
ps_load_config && ps_choose_base && ps_unlocked && ps_prepare_base || exit 1
ps_pick_priority
echo "Native root/kernel test; zRAM minimum priority=$PS_ZRAM_MIN"
ps_probe
RESULT=$?
# The probe removes its file only after successful swapoff, so it is safe to
# remove the marker and empty directory only when the probe no longer exists.
if [ ! -e "$PS_BASE/.probe.swap" ]; then
    ps_tool rm -f "$PS_BASE/.pocketswap-owner"
    ps_tool rmdir "$PS_BASE"
fi
ps_tool cat "$PS_SWAPS"
echo "Native 4MiB probe result=$RESULT"
exit "$RESULT"
