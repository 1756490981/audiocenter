using System;
using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IAudioEndpointVolume
{
	int RegisterControlChangeNotify(nint notify);

	int UnregisterControlChangeNotify(nint notify);

	uint GetChannelCount();

	int SetMasterVolumeLevel(float levelDB, ref Guid eventContext);

	int SetMasterVolumeLevelScalar(float level, ref Guid eventContext);

	int GetMasterVolumeLevel(out float levelDB);

	int GetMasterVolumeLevelScalar(out float level);

	int SetChannelVolumeLevel(uint channel, float levelDB, ref Guid eventContext);

	int SetChannelVolumeLevelScalar(uint channel, float level, ref Guid eventContext);

	int GetChannelVolumeLevel(uint channel, out float levelDB);

	float GetChannelVolumeLevelScalar(uint channel);

	int SetMute(int mute, ref Guid eventContext);

	int GetMute();

	int GetVolumeStepInfo(out uint step, out uint stepCount);

	int VolumeStepUp(ref Guid eventContext);

	int VolumeStepDown(ref Guid eventContext);

	int QueryHardwareSupport(out uint support);

	int GetVolumeRange(out float min, out float max, out float inc);
}
