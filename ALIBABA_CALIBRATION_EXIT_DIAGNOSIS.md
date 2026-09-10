# Alibaba calibration exit diagnosis

**Result: `EXTERNAL_SYSTEM_SHUTDOWN` (confirmed).**

The last complete formal status was **28,755 / 48,600** trajectories at
2026-09-10 04:29:05 +08:00. Windows event 1074 then records
`MoUsoCoreWorker.exe` requesting a planned restart at 04:29:14, followed by a
second planned OS-upgrade restart request from `TrustedInstaller` at 04:33:06.
Event 6006 and Kernel-General events 13/12 show a normal shutdown and boot.
Windows Update subsequently recorded installation of KB5126052 and KB5124008.

The runner PID 32776 and worker PIDs 30440/28848 did not survive the reboot.
There is no Python/CUDA traceback, contemporaneous Application Error 1000,
disk/NTFS error, new scientific mismatch, or failure record for this
interruption. Process exit codes cannot be recovered after an operating-system
restart.

The frozen scientific files, configuration files, pool manifest, Alibaba pool
manifest, and original joint-DAG executor still match their recorded SHA-256
values. The interruption is therefore an execution-environment event, not a
scientific failure.

Machine-readable evidence is in
`audits/alibaba_calibration_exit_diagnosis.json`.
