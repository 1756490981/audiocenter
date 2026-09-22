using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("7997E22A-F1E1-4D6E-8A84-EEA2B8B63EB9")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IAudioMute
{
	int GetMute(out int muted);

	int SetMute(int muted, nint context);
}
