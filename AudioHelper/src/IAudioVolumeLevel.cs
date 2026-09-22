using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("45C37CAA-3B53-444A-9C69-6B279FB6EB2E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IAudioVolumeLevel
{
	int GetChannelCount(out uint count);

	int GetLevel(uint channel, out float level);

	int GetLevelRange(uint channel, out float min, out float max, out float inc);

	int SetLevel(uint channel, float level, nint context);

	int SetLevelAllChannels(float level, nint context);

	int SetLevelUniform(float level, nint context);
}
