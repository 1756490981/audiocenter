namespace AudioHelper;

internal record SessionInfo(uint pid, string processName, string displayName, int volume, bool muted, string? deviceId, string? icon);
