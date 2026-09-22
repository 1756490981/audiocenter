using System.Collections.Generic;

namespace AudioHelper;

internal record ProfileData
{
	public string? Name { get; set; }

	public string? CreatedAt { get; set; }

	public int? MasterVolume { get; set; }

	public bool? MasterMuted { get; set; }

	public string? DefaultRenderDeviceId { get; set; }

	public string? DefaultCaptureDeviceId { get; set; }

	public Dictionary<string, ProfileDeviceVolume>? DeviceVolumes { get; set; }

	public Dictionary<string, string>? DeviceStates { get; set; }

	public Dictionary<uint, string>? SessionRouting { get; set; }

	public Dictionary<string, string>? SessionRoutingByProcess { get; set; }

	public Dictionary<uint, ProfileDeviceVolume>? SessionVolumes { get; set; }
}
