using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface ISimpleAudioVolume
{
	int SetMasterVolume(float level, nint context);

	int GetMasterVolume(out float level);

	int SetMute(int mute, nint context);

	int GetMute(out int mute);
}
