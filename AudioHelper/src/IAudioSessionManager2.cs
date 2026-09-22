using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("BFA971F1-4D5E-40BB-935E-967039BFBEE4")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IAudioSessionManager2
{
	int GetAudioSessionControl(nint audioSessionGuid, int streamFlags, out nint session);

	int GetSimpleAudioVolume(nint audioSessionGuid, int streamFlags, out nint audioVolume);

	int GetSessionEnumerator(out nint enumerator);

	int RegisterSessionNotification(nint notification);

	int UnregisterSessionNotification(nint notification);

	int RegisterDuckNotification(string sessionId, nint notification);

	int UnregisterDuckNotification(nint notification);
}
