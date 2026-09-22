using System;
using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("f8679f50-850a-41cf-9c72-430f290290c8")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IPolicyConfig
{
	void GetMixFormat([MarshalAs(UnmanagedType.LPWStr)] string deviceId, out nint ppFormat);

	void GetDeviceFormat([MarshalAs(UnmanagedType.LPWStr)] string deviceId, [MarshalAs(UnmanagedType.Bool)] bool isDefault, out nint ppFormat);

	void ResetDeviceFormat([MarshalAs(UnmanagedType.LPWStr)] string deviceId);

	void SetDeviceFormat([MarshalAs(UnmanagedType.LPWStr)] string deviceId, nint pEndpointFormat, nint pMixFormat);

	void GetProcessingPeriod([MarshalAs(UnmanagedType.LPWStr)] string deviceId, [MarshalAs(UnmanagedType.Bool)] bool isDefault, out long pDefaultPeriod, out long pMinPeriod);

	void SetProcessingPeriod([MarshalAs(UnmanagedType.LPWStr)] string deviceId, ref long pDefaultPeriod, ref long pMinPeriod);

	void GetShareMode([MarshalAs(UnmanagedType.LPWStr)] string deviceId, out nint pMode);

	void SetShareMode([MarshalAs(UnmanagedType.LPWStr)] string deviceId, ref Guid pMode);

	void GetPropertyValue([MarshalAs(UnmanagedType.LPWStr)] string deviceId, ref PropertyKey pkey, ref PROPVARIANT pv);

	void SetPropertyValue([MarshalAs(UnmanagedType.LPWStr)] string deviceId, ref PropertyKey pkey, ref PROPVARIANT pv);

	void SetDefaultEndpoint([MarshalAs(UnmanagedType.LPWStr)] string deviceId, ERole eRole);

	void SetEndpointVisibility([MarshalAs(UnmanagedType.LPWStr)] string deviceId, short isVisible);
}
