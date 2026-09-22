using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IMMDeviceEnumerator
{
	int EnumAudioEndpoints(int dataFlow, int stateMask, out nint devices);

	int GetDefaultAudioEndpoint(int dataFlow, int role, out nint device);

	int GetDevice(string id, out nint device);

	int RegisterEndpointNotificationCallback(nint client);

	int UnregisterEndpointNotificationCallback(nint client);
}
