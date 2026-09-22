namespace AudioHelper;

internal record Command(string cmd, long? rid = null, string? type = null, string? id = null, string? deviceId = null, uint pid = 0u, float volume = 0f, bool mute = false, string? name = null, bool? enabled = null, string? playbackDeviceId = null, int? sampleRate = null, int? bitDepth = null, int? channels = null, string? profileName = null, string? destPath = null, string? sourcePath = null);
