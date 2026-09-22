using System;
using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IAudioSessionControl2
{
	[return: MarshalAs(UnmanagedType.I4)]
	int GetState();

	[return: MarshalAs(UnmanagedType.LPWStr)]
	string GetDisplayName();

	void SetDisplayName([MarshalAs(UnmanagedType.LPWStr)] string name, ref Guid eventContext);

	[return: MarshalAs(UnmanagedType.LPWStr)]
	string GetIconPath();

	void SetIconPath([MarshalAs(UnmanagedType.LPWStr)] string path, ref Guid eventContext);

	void GetGroupingParam(out Guid param);

	void SetGroupingParam(ref Guid param, ref Guid eventContext);

	void RegisterAudioSessionNotification(nint notification);

	void UnregisterAudioSessionNotification(nint notification);

	void GetSessionIdentifier([MarshalAs(UnmanagedType.LPWStr)] out string id);

	void GetSessionInstanceIdentifier([MarshalAs(UnmanagedType.LPWStr)] out string id);

	[PreserveSig]
	int GetProcessId(out uint pid);

	[PreserveSig]
	int IsSystemSoundsSession();

	void SetDuckingPreference(int enabled);
}
