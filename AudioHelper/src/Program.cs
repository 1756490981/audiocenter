using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace AudioHelper;

internal class Program
{
	private static Guid CLSID_MMDeviceEnumerator = new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E");

	private static Guid IID_IMMDeviceEnumerator = new Guid("A95664D2-9614-4F35-A746-DE8DB63617E6");

	private static Guid IID_IAudioEndpointVolume = new Guid("5CDF2C82-841E-4546-9722-0CF74078229A");

	private static Guid IID_IAudioSessionManager2 = new Guid("BFA971F1-4D5E-40BB-935E-967039BFBEE4");

	private static Guid IID_IDeviceTopology = new Guid("2A07407E-6497-4A18-9787-32F79BD0D98F");

	private static Guid IID_IAudioVolumeLevel = new Guid("45C37CAA-3B53-444A-9C69-6B279FB6EB2E");

	private static Guid IID_IAudioPolicyConfigFactory = new Guid("2a59116d-6c4f-45e0-a74f-707e3fef9258");

	private static Guid IID_IAudioPolicyConfigFactory21H2 = new Guid("ab3d4648-e242-459f-b02f-541c70306324");

	private const string DEVINTERFACE_AUDIO_RENDER = "#{e6327cad-dcec-4949-ae8a-991e976a79d2}";

	private const string DEVINTERFACE_AUDIO_CAPTURE = "#{2eef81be-33fa-4800-9670-1cd474972c3f}";

	private const string MMDEVAPI_TOKEN = "\\\\?\\SWD#MMDEVAPI#";

	private static readonly JsonSerializerOptions JsonOptions = new JsonSerializerOptions
	{
		PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
		PropertyNameCaseInsensitive = true
	};

	private static Guid KSNODETYPE_VOLUME = new Guid("6BDDA5A1-554A-456B-9FD3-0A6AC1B6EFB3");

	private static Guid KSNODETYPE_MUTE = new Guid("1ADD7C43-6F2D-4A10-BA72-AD796BB02E02");

	private static Guid GUID_NULL = Guid.Empty;

	private static Guid ListenPropertyGuid = new Guid("{24DBB0FC-9311-4B3D-9CF0-18FF155639D4}");

	private static Guid PKEY_AudioEngine_DeviceFormat = new Guid("{F19F064D-082C-4E27-BC73-6882A1BB8E4C}");

	private static Guid PKEY_AudioEngine_OEMFormat = new Guid("{E4870E26-3CC5-4CD2-BA46-CA0A9A70ED04}");

	private static Guid KSDATAFORMAT_SUBTYPE_PCM = new Guid("{00000001-0000-0010-8000-00AA00389B71}");

	private static nint _policyConfigFactory;

	private static bool _policyConfigAvailable;

	private static bool _policyConfigChecked;

	private static SetPersistedDefaultAudioEndpointDelegate _setPersistedDefaultAudioEndpoint;

	private static GetPersistedDefaultAudioEndpointDelegate _getPersistedDefaultAudioEndpoint;

	private static string ProfileDir => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AudioCenter", "profiles");

	[DllImport("shlwapi.dll", CharSet = CharSet.Unicode)]
	private static extern int SHLoadIndirectString(string pszSource, StringBuilder pszOutBuf, int cchOutBuf, nint ppvReserved);

	[DllImport("winmm.dll")]
	private static extern int waveOutGetVolume(nint uDeviceID, out uint dwVolume);

	[DllImport("winmm.dll")]
	private static extern int waveOutSetVolume(nint uDeviceID, uint dwVolume);

	[DllImport("combase.dll", PreserveSig = false)]
	private static extern void RoGetActivationFactory(nint activatableClassId, [In] ref Guid iid, out nint factory);

	[DllImport("combase.dll", PreserveSig = false)]
	private static extern void WindowsCreateString([MarshalAs(UnmanagedType.LPWStr)] string src, [In] uint length, out nint hstring);

	[DllImport("combase.dll", PreserveSig = false)]
	private static extern void WindowsDeleteString(nint hstring);

	[DllImport("combase.dll")]
	private static extern nint WindowsGetStringRawBuffer(nint hstring, out uint length);

	private static void Main(string[] args)
	{
		using StreamReader streamReader = new StreamReader(Console.OpenStandardInput(), Encoding.UTF8);
		using StreamWriter streamWriter = new StreamWriter(Console.OpenStandardOutput(), Encoding.UTF8)
		{
			AutoFlush = true
		};
		string json;
		while ((json = streamReader.ReadLine()) != null)
		{
			try
			{
				Command command = JsonSerializer.Deserialize<Command>(json, JsonOptions);
				string text = ExecuteCommand(command);
				if (command.rid.HasValue)
				{
					Dictionary<string, JsonElement>? dictionary = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(text);
					dictionary["id"] = JsonSerializer.SerializeToElement(command.rid.Value);
					text = JsonSerializer.Serialize(dictionary);
				}
				streamWriter.WriteLine(text);
			}
			catch (Exception ex)
			{
				streamWriter.WriteLine(Json(new
				{
					error = ex.Message
				}));
			}
		}
	}

	private static string Json(object anon)
	{
		JsonObject jsonObject = new JsonObject();
		PropertyInfo[] properties = anon.GetType().GetProperties();
		foreach (PropertyInfo obj in properties)
		{
			object value = obj.GetValue(anon);
			JsonObject jsonObject2 = jsonObject;
			string name = obj.Name;
			JsonNode value2 = ((value == null) ? null : ((value is string value3) ? JsonValue.Create(value3) : ((value is int value4) ? JsonValue.Create(value4) : ((value is long value5) ? JsonValue.Create(value5) : ((value is float value6) ? JsonValue.Create(value6) : ((value is double value7) ? JsonValue.Create(value7) : ((!(value is bool value8)) ? JsonSerializer.SerializeToNode(value, value.GetType()) : JsonValue.Create(value8))))))));
			jsonObject2[name] = value2;
		}
		return jsonObject.ToJsonString();
	}

	private static string ExecuteCommand(Command cmd)
	{
		IMMDeviceEnumerator iMMDeviceEnumerator = (IMMDeviceEnumerator)Activator.CreateInstance(Type.GetTypeFromCLSID(CLSID_MMDeviceEnumerator));
		return cmd.cmd switch
		{
			"list-devices" => ListDevices(iMMDeviceEnumerator, cmd), 
			"set-default-device" => SetDefaultDevice(iMMDeviceEnumerator, cmd), 
			"list-sessions" => ListSessions(iMMDeviceEnumerator), 
			"set-session-volume" => SetSessionVolume(iMMDeviceEnumerator, cmd), 
			"set-session-mute" => SetSessionMute(iMMDeviceEnumerator, cmd), 
			"get-master-volume" => GetMasterVolume(iMMDeviceEnumerator), 
			"set-master-volume" => SetMasterVolume(iMMDeviceEnumerator, cmd), 
			"set-master-mute" => SetMasterMute(iMMDeviceEnumerator, cmd), 
			"debug-volume" => DebugVolume(iMMDeviceEnumerator, cmd), 
			"debug-topo" => DebugTopo(iMMDeviceEnumerator, cmd), 
			"set-session-device" => SetSessionDevice(iMMDeviceEnumerator, cmd), 
			"get-session-device" => GetSessionDevice(iMMDeviceEnumerator, cmd), 
			"debug-sessions" => DebugSessions(iMMDeviceEnumerator), 
			"get-device-volume" => GetDeviceVolume(iMMDeviceEnumerator, cmd), 
			"set-device-volume" => SetDeviceVolume(iMMDeviceEnumerator, cmd), 
			"set-device-mute" => SetDeviceMute(iMMDeviceEnumerator, cmd), 
			"get-listen" => GetListen(iMMDeviceEnumerator, cmd), 
			"set-listen" => SetListen(iMMDeviceEnumerator, cmd), 
			"get-device-format" => GetDeviceFormat(iMMDeviceEnumerator, cmd), 
			"set-device-format" => SetDeviceFormat(iMMDeviceEnumerator, cmd), 
			"save-profile" => SaveProfile(iMMDeviceEnumerator, cmd), 
			"load-profile" => LoadProfile(iMMDeviceEnumerator, cmd), 
			"list-profiles" => ListProfiles(iMMDeviceEnumerator), 
			"delete-profile" => DeleteProfile(iMMDeviceEnumerator, cmd), 
			"export-profile" => ExportProfile(iMMDeviceEnumerator, cmd), 
			"import-profile" => ImportProfile(iMMDeviceEnumerator, cmd), 
			"set-device-enabled" => SetDeviceEnabled(iMMDeviceEnumerator, cmd), 
			"max-all-volumes" => MaxAllVolumes(iMMDeviceEnumerator), 
			_ => Json(new
			{
				error = "unknown command: " + cmd.cmd
			}), 
		};
	}

	private static string ListDevices(IMMDeviceEnumerator enumerator, Command cmd)
	{
		EDataFlow dataFlow = ((cmd.type == "capture") ? EDataFlow.eCapture : EDataFlow.eRender);
		int stateMask = 11;
		enumerator.EnumAudioEndpoints((int)dataFlow, stateMask, out var devices);
		List<DeviceInfo> list = new List<DeviceInfo>();
		string text = null;
		try
		{
			enumerator.GetDefaultAudioEndpoint((int)dataFlow, 0, out var device);
			if (device != IntPtr.Zero)
			{
				((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).GetId(out var id);
				text = Marshal.PtrToStringUni(id);
				Marshal.Release(device);
				Marshal.FreeCoTaskMem(id);
			}
		}
		catch
		{
		}
		if (devices != IntPtr.Zero)
		{
			IMMDeviceCollection iMMDeviceCollection = (IMMDeviceCollection)Marshal.GetTypedObjectForIUnknown(devices, typeof(IMMDeviceCollection));
			iMMDeviceCollection.GetCount(out var count);
			for (int i = 0; i < count; i++)
			{
				iMMDeviceCollection.Item(i, out var device2);
				IMMDevice obj2 = (IMMDevice)Marshal.GetTypedObjectForIUnknown(device2, typeof(IMMDevice));
				obj2.GetId(out var id2);
				obj2.GetState(out var state);
				string text2 = Marshal.PtrToStringUni(id2) ?? "";
				string deviceName = GetDeviceName(obj2);
				List<DeviceInfo> list2 = list;
				string id3 = text2;
				string name = deviceName ?? "未知设备";
				bool isDefault = text2 == text;
				list2.Add(new DeviceInfo(id3, name, isDefault, state switch
				{
					1 => "active", 
					2 => "disabled", 
					4 => "not-present", 
					8 => "unplugged", 
					_ => "unknown", 
				}));
				Marshal.FreeCoTaskMem(id2);
				Marshal.Release(device2);
			}
			Marshal.Release(devices);
		}
		return Json(new
		{
			devices = list
		});
	}

	private static string GetDeviceName(IMMDevice device)
	{
		try
		{
			device.OpenPropertyStore(0, out var properties);
			IPropertyStore obj = (IPropertyStore)Marshal.GetTypedObjectForIUnknown(properties, typeof(IPropertyStore));
			PropertyKey key = new PropertyKey(new Guid("{A45C254E-DF1C-4EFD-8020-67D146A850E0}"), 14);
			obj.GetValue(ref key, out var value);
			string text = (string)value.Value;
			Marshal.Release(properties);
			int num = text.LastIndexOf(" (");
			if (num > 0)
			{
				text = text.Substring(0, num);
			}
			return text;
		}
		catch
		{
			return "未知设备";
		}
	}

	private static string ResolveIndirectString(string raw)
	{
		try
		{
			StringBuilder stringBuilder = new StringBuilder(512);
			if (SHLoadIndirectString(raw, stringBuilder, stringBuilder.Capacity, IntPtr.Zero) == 0)
			{
				return stringBuilder.ToString();
			}
		}
		catch
		{
		}
		if (!raw.Contains(",-"))
		{
			return raw;
		}
		return raw.Split(",-")[0].TrimStart('@').Split('\\').Last()
			.Split('.')
			.First();
	}

	private static string? ResolveIconPath(string raw)
	{
		try
		{
			if (string.IsNullOrEmpty(raw))
			{
				return null;
			}
			if (raw.StartsWith('@'))
			{
				raw = raw.Substring(1);
				if (raw.Contains('%'))
				{
					raw = Environment.ExpandEnvironmentVariables(raw);
				}
				int num = raw.LastIndexOf(",-");
				if (num > 0)
				{
					raw = raw.Substring(0, num);
				}
				return File.Exists(raw) ? raw : null;
			}
			return File.Exists(raw) ? raw : null;
		}
		catch
		{
			return null;
		}
	}

	private static string SetDefaultDevice(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			IPolicyConfig obj = (IPolicyConfig)new PolicyConfigClient();
			obj.SetDefaultEndpoint(cmd.id, ERole.eConsole);
			obj.SetDefaultEndpoint(cmd.id, ERole.eMultimedia);
			obj.SetDefaultEndpoint(cmd.id, ERole.eCommunications);
			return Json(new
			{
				success = true
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = "设置失败: " + ex.Message + ". 可能需要以管理员权限运行"
			});
		}
	}

	private static string ListSessions(IMMDeviceEnumerator enumerator)
	{
		Dictionary<uint, (ISimpleAudioVolume, IAudioSessionControl2)> dictionary = new Dictionary<uint, (ISimpleAudioVolume, IAudioSessionControl2)>();
		Dictionary<uint, (string, string, string)> dictionary2 = new Dictionary<uint, (string, string, string)>();
		int stateMask = 11;
		enumerator.EnumAudioEndpoints(0, stateMask, out var devices);
		if (devices != IntPtr.Zero)
		{
			IMMDeviceCollection iMMDeviceCollection = (IMMDeviceCollection)Marshal.GetTypedObjectForIUnknown(devices, typeof(IMMDeviceCollection));
			iMMDeviceCollection.GetCount(out var count);
			for (int i = 0; i < count; i++)
			{
				iMMDeviceCollection.Item(i, out var device);
				IMMDevice iMMDevice = (IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice));
				iMMDevice.GetState(out var state);
				if (state != 1)
				{
					Marshal.Release(device);
					continue;
				}
				try
				{
					iMMDevice.Activate(ref IID_IAudioSessionManager2, 1, IntPtr.Zero, out var pInterface);
					((IAudioSessionManager2)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioSessionManager2))).GetSessionEnumerator(out var enumerator2);
					IAudioSessionEnumerator audioSessionEnumerator = (IAudioSessionEnumerator)Marshal.GetTypedObjectForIUnknown(enumerator2, typeof(IAudioSessionEnumerator));
					audioSessionEnumerator.GetCount(out var count2);
					for (int j = 0; j < count2; j++)
					{
						audioSessionEnumerator.GetSession(j, out var session);
						IAudioSessionControl2 audioSessionControl = (IAudioSessionControl2)Marshal.GetTypedObjectForIUnknown(session, typeof(IAudioSessionControl2));
						audioSessionControl.GetProcessId(out var pid);
						if (!dictionary.ContainsKey(pid))
						{
							try
							{
								ISimpleAudioVolume item = (ISimpleAudioVolume)Marshal.GetTypedObjectForIUnknown(session, typeof(ISimpleAudioVolume));
								dictionary[pid] = (item, audioSessionControl);
								string displayName = audioSessionControl.GetDisplayName();
								string text = displayName;
								if (!string.IsNullOrEmpty(displayName))
								{
									text = (displayName.StartsWith('@') ? ResolveIndirectString(displayName) : displayName);
								}
								string text2 = "";
								try
								{
									text2 = Process.GetProcessById((int)pid).ProcessName + ".exe";
								}
								catch
								{
									text2 = $"PID:{pid}";
								}
								if (string.IsNullOrEmpty(text))
								{
									text = text2;
								}
								if (string.IsNullOrEmpty(text))
								{
									text = $"PID:{pid}";
								}
								string text3 = null;
								try
								{
									string iconPath = audioSessionControl.GetIconPath();
									if (!string.IsNullOrEmpty(iconPath))
									{
										text3 = ResolveIconPath(iconPath);
									}
									if (string.IsNullOrEmpty(text3) && pid != 0)
									{
										try
										{
											text3 = Process.GetProcessById((int)pid).MainModule?.FileName;
										}
										catch
										{
										}
									}
								}
								catch
								{
								}
								dictionary2[pid] = (text2, text, text3);
							}
							catch
							{
							}
						}
						Marshal.Release(session);
					}
					Marshal.Release(enumerator2);
					Marshal.Release(pInterface);
				}
				catch
				{
				}
				Marshal.Release(device);
			}
			Marshal.Release(devices);
		}
		List<SessionInfo> list = new List<SessionInfo>();
		foreach (KeyValuePair<uint, (ISimpleAudioVolume, IAudioSessionControl2)> item3 in dictionary)
		{
			uint key = item3.Key;
			ISimpleAudioVolume item2 = item3.Value.Item1;
			if (!dictionary2.TryGetValue(key, out var value))
			{
				continue;
			}
			float level = 1f;
			int mute = 0;
			try
			{
				item2.GetMasterVolume(out level);
			}
			catch
			{
			}
			try
			{
				item2.GetMute(out mute);
			}
			catch
			{
			}
			string deviceId = null;
			try
			{
				EnsurePolicyConfig();
				if (_policyConfigAvailable && _getPersistedDefaultAudioEndpoint(_policyConfigFactory, key, EDataFlow.eRender, ERole.eMultimedia, out var deviceId2) >= 0)
				{
					deviceId = UnpackDeviceId(ReadHString(deviceId2));
				}
			}
			catch
			{
			}
			list.Add(new SessionInfo(key, value.Item1, value.Item2, (int)(level * 100f), mute != 0, deviceId, value.Item3));
		}
		return Json(new
		{
			sessions = list.OrderBy((SessionInfo s) => s.displayName).ToList()
		});
	}

	private static string SetSessionVolume(IMMDeviceEnumerator enumerator, Command cmd)
	{
		List<ISimpleAudioVolume> list = FindAllSessionVolumes(enumerator, cmd.pid);
		if (list.Count == 0)
		{
			return Json(new
			{
				error = "session not found"
			});
		}
		float level = cmd.volume / 100f;
		foreach (ISimpleAudioVolume item in list)
		{
			item.SetMasterVolume(level, IntPtr.Zero);
		}
		return Json(new
		{
			success = true
		});
	}

	private static string SetSessionMute(IMMDeviceEnumerator enumerator, Command cmd)
	{
		List<ISimpleAudioVolume> list = FindAllSessionVolumes(enumerator, cmd.pid);
		if (list.Count == 0)
		{
			return Json(new
			{
				error = "session not found"
			});
		}
		foreach (ISimpleAudioVolume item in list)
		{
			item.SetMute(cmd.mute ? 1 : 0, IntPtr.Zero);
		}
		return Json(new
		{
			success = true
		});
	}

	private static List<ISimpleAudioVolume> FindAllSessionVolumes(IMMDeviceEnumerator enumerator, uint targetPid)
	{
		List<ISimpleAudioVolume> list = new List<ISimpleAudioVolume>();
		int stateMask = 11;
		enumerator.EnumAudioEndpoints(0, stateMask, out var devices);
		if (devices == IntPtr.Zero)
		{
			return list;
		}
		IMMDeviceCollection iMMDeviceCollection = (IMMDeviceCollection)Marshal.GetTypedObjectForIUnknown(devices, typeof(IMMDeviceCollection));
		iMMDeviceCollection.GetCount(out var count);
		for (int i = 0; i < count; i++)
		{
			iMMDeviceCollection.Item(i, out var device);
			IMMDevice iMMDevice = (IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice));
			iMMDevice.GetState(out var state);
			if (state != 1)
			{
				Marshal.Release(device);
				continue;
			}
			try
			{
				iMMDevice.Activate(ref IID_IAudioSessionManager2, 1, IntPtr.Zero, out var pInterface);
				((IAudioSessionManager2)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioSessionManager2))).GetSessionEnumerator(out var enumerator2);
				IAudioSessionEnumerator audioSessionEnumerator = (IAudioSessionEnumerator)Marshal.GetTypedObjectForIUnknown(enumerator2, typeof(IAudioSessionEnumerator));
				audioSessionEnumerator.GetCount(out var count2);
				for (int j = 0; j < count2; j++)
				{
					audioSessionEnumerator.GetSession(j, out var session);
					((IAudioSessionControl2)Marshal.GetTypedObjectForIUnknown(session, typeof(IAudioSessionControl2))).GetProcessId(out var pid);
					if (pid == targetPid)
					{
						ISimpleAudioVolume item = (ISimpleAudioVolume)Marshal.GetTypedObjectForIUnknown(session, typeof(ISimpleAudioVolume));
						list.Add(item);
					}
					Marshal.Release(session);
				}
				Marshal.Release(enumerator2);
				Marshal.Release(pInterface);
			}
			catch
			{
			}
			Marshal.Release(device);
		}
		Marshal.Release(devices);
		return list;
	}

	private static string GetMasterVolume(IMMDeviceEnumerator enumerator)
	{
		try
		{
			enumerator.GetDefaultAudioEndpoint(0, 0, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface);
			IAudioEndpointVolume obj = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
			obj.GetMasterVolumeLevelScalar(out var level);
			int mute = obj.GetMute();
			Marshal.Release(pInterface);
			Marshal.Release(device);
			return Json(new
			{
				volume = (int)(level * 100f),
				muted = (mute != 0),
				hasEndpointVolume = true
			});
		}
		catch
		{
		}
		try
		{
			if (waveOutGetVolume(new IntPtr(-1), out var dwVolume) == 0)
			{
				uint num = dwVolume & 0xFFFF;
				uint num2 = (dwVolume >> 16) & 0xFFFF;
				int num3 = (int)((float)(num + num2) / 2f / 65535f * 100f);
				bool hasEndpointVolume = false;
				try
				{
					enumerator.GetDefaultAudioEndpoint(0, 0, out var device2);
					((IMMDevice)Marshal.GetTypedObjectForIUnknown(device2, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface2);
					((IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface2, typeof(IAudioEndpointVolume))).GetVolumeRange(out var min, out var max, out var _);
					hasEndpointVolume = max > min;
					Marshal.Release(pInterface2);
					Marshal.Release(device2);
				}
				catch
				{
				}
				return Json(new
				{
					volume = num3,
					muted = (num3 == 0),
					hasEndpointVolume = hasEndpointVolume
				});
			}
		}
		catch
		{
		}
		return Json(new
		{
			volume = 100,
			muted = false,
			hasEndpointVolume = false
		});
	}

	private static string SetMasterVolume(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			enumerator.GetDefaultAudioEndpoint(0, 0, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface);
			IAudioEndpointVolume obj = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
			Guid eventContext = Guid.Empty;
			obj.SetMasterVolumeLevelScalar(cmd.volume / 100f, ref eventContext);
			Marshal.Release(pInterface);
			Marshal.Release(device);
			return Json(new
			{
				success = true,
				mode = "endpoint"
			});
		}
		catch
		{
		}
		try
		{
			nint uDeviceID = new IntPtr(-1);
			uint num = (uint)(cmd.volume / 100f * 65535f);
			uint dwVolume = num | (num << 16);
			if (waveOutSetVolume(uDeviceID, dwVolume) == 0)
			{
				return Json(new
				{
					success = true,
					mode = "waveOut"
				});
			}
		}
		catch
		{
		}
		try
		{
			enumerator.GetDefaultAudioEndpoint(0, 0, out var device2);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device2, typeof(IMMDevice))).Activate(ref IID_IAudioSessionManager2, 1, IntPtr.Zero, out var pInterface2);
			((IAudioSessionManager2)Marshal.GetTypedObjectForIUnknown(pInterface2, typeof(IAudioSessionManager2))).GetSessionEnumerator(out var enumerator2);
			IAudioSessionEnumerator audioSessionEnumerator = (IAudioSessionEnumerator)Marshal.GetTypedObjectForIUnknown(enumerator2, typeof(IAudioSessionEnumerator));
			audioSessionEnumerator.GetCount(out var count);
			float level = cmd.volume / 100f;
			for (int i = 0; i < count; i++)
			{
				audioSessionEnumerator.GetSession(i, out var session);
				try
				{
					((ISimpleAudioVolume)Marshal.GetTypedObjectForIUnknown(session, typeof(ISimpleAudioVolume))).SetMasterVolume(level, IntPtr.Zero);
				}
				catch
				{
				}
				Marshal.Release(session);
			}
			Marshal.Release(enumerator2);
			Marshal.Release(pInterface2);
			Marshal.Release(device2);
			return Json(new
			{
				success = true,
				mode = "session"
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = "无法设置音量: " + ex.Message
			});
		}
	}

	private static string SetMasterMute(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			enumerator.GetDefaultAudioEndpoint(0, 0, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface);
			IAudioEndpointVolume obj = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
			Guid eventContext = Guid.Empty;
			obj.SetMute(cmd.mute ? 1 : 0, ref eventContext);
			Marshal.Release(pInterface);
			Marshal.Release(device);
			return Json(new
			{
				success = true,
				mode = "endpoint"
			});
		}
		catch
		{
		}
		try
		{
			nint uDeviceID = new IntPtr(-1);
			if (cmd.mute)
			{
				waveOutSetVolume(uDeviceID, 0u);
			}
			else
			{
				uint num = 32767u;
				waveOutSetVolume(uDeviceID, num | (num << 16));
			}
			return Json(new
			{
				success = true,
				mode = "waveOut"
			});
		}
		catch
		{
		}
		return Json(new
		{
			error = "无法设置静音"
		});
	}

	private static string DebugVolume(IMMDeviceEnumerator enumerator, Command cmd)
	{
		List<object> list = new List<object>();
		try
		{
			uint num = (uint)(cmd.volume / 100f * 65535f);
			nint uDeviceID = new IntPtr(-1);
			int value = waveOutGetVolume(uDeviceID, out var dwVolume);
			list.Add(new
			{
				method = "waveOut",
				step = "get",
				hr = $"0x{value:X}",
				left = (dwVolume & 0xFFFF),
				right = ((dwVolume >> 16) & 0xFFFF)
			});
			int value2 = waveOutSetVolume(uDeviceID, num | (num << 16));
			waveOutGetVolume(uDeviceID, out var dwVolume2);
			list.Add(new
			{
				method = "waveOut",
				step = "set",
				target = $"0x{num:X}",
				setHr = $"0x{value2:X}",
				after = $"0x{dwVolume2:X}"
			});
		}
		catch (Exception ex)
		{
			list.Add(new
			{
				method = "waveOut",
				error = ex.Message
			});
		}
		int[] array = new int[5] { 1, 2, 3, 7, 23 };
		foreach (int clsCtx in array)
		{
			try
			{
				enumerator.GetDefaultAudioEndpoint(0, 0, out var device);
				if (device == IntPtr.Zero)
				{
					continue;
				}
				((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, clsCtx, IntPtr.Zero, out var pInterface);
				if (pInterface != IntPtr.Zero)
				{
					IAudioEndpointVolume audioEndpointVolume = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
					try
					{
						float level = cmd.volume / 100f;
						Guid eventContext = Guid.Empty;
						int value3 = audioEndpointVolume.SetMasterVolumeLevelScalar(level, ref eventContext);
						audioEndpointVolume.GetMasterVolumeLevelScalar(out var level2);
						list.Add(new
						{
							method = "IAudioEndpointVolume",
							clsCtx = clsCtx,
							setHr = $"0x{value3:X}",
							currentVolume = level2
						});
					}
					catch (Exception ex2)
					{
						list.Add(new
						{
							method = "IAudioEndpointVolume",
							clsCtx = clsCtx,
							error = ex2.Message
						});
					}
					Marshal.Release(pInterface);
				}
				Marshal.Release(device);
			}
			catch (Exception ex3)
			{
				list.Add(new
				{
					method = "IAudioEndpointVolume",
					clsCtx = clsCtx,
					error = ex3.Message
				});
			}
		}
		return Json(new
		{
			results = list
		});
	}

	private static void WalkTopology(IPart part, List<object> nodes, string indent = "")
	{
		part.GetPartType(out var type);
		part.GetSubType(out var type2);
		part.GetLocalId(out var id);
		Dictionary<string, object> dictionary = new Dictionary<string, object>
		{
			["localId"] = id,
			["partType"] = type.ToString()
		};
		if (type2 != GUID_NULL)
		{
			dictionary["subType"] = type2.ToString();
		}
		part.GetControlInterfaceCount(out var count);
		if (count != 0)
		{
			dictionary["controlCount"] = count;
		}
		nodes.Add(dictionary);
		part.EnumPartsOutgoing(out var parts);
		if (parts == IntPtr.Zero)
		{
			return;
		}
		IPartsList partsList = (IPartsList)Marshal.GetTypedObjectForIUnknown(parts, typeof(IPartsList));
		partsList.GetCount(out var count2);
		for (uint num = 0u; num < count2; num++)
		{
			partsList.GetPart(num, out var part2);
			if (part2 != IntPtr.Zero)
			{
				WalkTopology((IPart)Marshal.GetTypedObjectForIUnknown(part2, typeof(IPart)), nodes, indent + "  ");
				Marshal.Release(part2);
			}
		}
		Marshal.Release(parts);
	}

	private static string DebugTopo(IMMDeviceEnumerator enumerator, Command cmd)
	{
		List<object> list = new List<object>();
		nint device = IntPtr.Zero;
		try
		{
			enumerator.GetDefaultAudioEndpoint(0, 0, out device);
			list.Add(new
			{
				phase = "init",
				status = "got default device"
			});
		}
		catch (Exception ex)
		{
			list.Add(new
			{
				phase = "init",
				error = ex.Message
			});
			return Json(new
			{
				results = list
			});
		}
		IMMDevice iMMDevice = (IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice));
		try
		{
			iMMDevice.Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface);
			if (pInterface != IntPtr.Zero)
			{
				IAudioEndpointVolume audioEndpointVolume = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
				uint support = 0u;
				try
				{
					audioEndpointVolume.QueryHardwareSupport(out support);
				}
				catch (Exception ex2)
				{
					list.Add(new
					{
						phase = "endpoint_diag",
						method = "QueryHardwareSupport",
						error = ex2.Message
					});
				}
				float min = 0f;
				float max = 0f;
				float inc = 0f;
				try
				{
					audioEndpointVolume.GetVolumeRange(out min, out max, out inc);
				}
				catch (Exception ex3)
				{
					list.Add(new
					{
						phase = "endpoint_diag",
						method = "GetVolumeRange",
						error = ex3.Message
					});
				}
				float level = 0f;
				try
				{
					audioEndpointVolume.GetMasterVolumeLevelScalar(out level);
				}
				catch (Exception ex4)
				{
					list.Add(new
					{
						phase = "endpoint_diag",
						method = "GetMasterVolumeLevelScalar",
						error = ex4.Message
					});
				}
				int num = 0;
				try
				{
					num = audioEndpointVolume.GetMute();
				}
				catch (Exception ex5)
				{
					list.Add(new
					{
						phase = "endpoint_diag",
						method = "GetMute",
						error = ex5.Message
					});
				}
				list.Add(new
				{
					phase = "endpoint_diag",
					hardwareSupport = $"0x{support:X}",
					hasHwVolume = ((support & 1) != 0),
					hasHwMute = ((support & 2) != 0),
					hasHwMeter = ((support & 4) != 0),
					volumeRangeDB = new
					{
						minDB = min,
						maxDB = max,
						incDB = inc
					},
					currentLevel = level,
					currentMute = (num != 0)
				});
				Marshal.Release(pInterface);
			}
		}
		catch (Exception ex6)
		{
			list.Add(new
			{
				phase = "activate_endpoint_volume",
				error = ex6.Message
			});
		}
		try
		{
			iMMDevice.Activate(ref IID_IDeviceTopology, 1, IntPtr.Zero, out var pInterface2);
			if (pInterface2 != IntPtr.Zero)
			{
				list.Add(new
				{
					phase = "topology",
					status = "activated"
				});
				IDeviceTopology deviceTopology = (IDeviceTopology)Marshal.GetTypedObjectForIUnknown(pInterface2, typeof(IDeviceTopology));
				deviceTopology.GetConnectorCount(out var count);
				list.Add(new
				{
					phase = "topology",
					connectorCount = count
				});
				for (uint num2 = 0u; num2 < count; num2++)
				{
					try
					{
						deviceTopology.GetConnector(num2, out var connector);
						if (connector != IntPtr.Zero)
						{
							IPart part = (IPart)Marshal.GetTypedObjectForIUnknown(connector, typeof(IPart));
							List<object> nodes = new List<object>();
							WalkTopology(part, nodes);
							list.Add(new
							{
								phase = "topology",
								connector = num2,
								nodes = nodes
							});
							Marshal.Release(connector);
						}
					}
					catch (Exception ex7)
					{
						list.Add(new
						{
							phase = "topology",
							connector = num2,
							error = ex7.Message
						});
					}
				}
				deviceTopology.GetSubunitCount(out var count2);
				list.Add(new
				{
					phase = "topology",
					subunitCount = count2
				});
				for (uint num3 = 0u; num3 < count2; num3++)
				{
					try
					{
						deviceTopology.GetSubunit(num3, out var subunit);
						if (subunit == IntPtr.Zero)
						{
							continue;
						}
						IPart part2 = (IPart)Marshal.GetTypedObjectForIUnknown(subunit, typeof(IPart));
						part2.GetPartType(out var type);
						part2.GetSubType(out var type2);
						list.Add(new
						{
							phase = "subunit",
							index = num3,
							partType = type.ToString(),
							subType = type2.ToString()
						});
						try
						{
							int num4 = part2.Activate(1, ref IID_IAudioVolumeLevel, out var obj);
							if (obj != IntPtr.Zero && num4 == 0)
							{
								IAudioVolumeLevel audioVolumeLevel = (IAudioVolumeLevel)Marshal.GetTypedObjectForIUnknown(obj, typeof(IAudioVolumeLevel));
								audioVolumeLevel.GetChannelCount(out var count3);
								List<object> list2 = new List<object>();
								for (uint num5 = 0u; num5 < count3; num5++)
								{
									audioVolumeLevel.GetLevelRange(num5, out var min2, out var max2, out var inc2);
									audioVolumeLevel.GetLevel(num5, out var level2);
									list2.Add(new
									{
										channel = num5,
										rangeDB = new
										{
											min = min2,
											max = max2,
											inc = inc2
										},
										currentDB = level2
									});
								}
								list.Add(new
								{
									phase = "volume_node",
									subunit = num3,
									channelCount = count3,
									channels = list2
								});
								if (cmd.volume > 0f)
								{
									list.Add(new
									{
										phase = "volume_node_test_skipped",
										note = "set test disabled to protect audio"
									});
								}
								Marshal.Release(obj);
							}
						}
						catch (Exception ex8)
						{
							list.Add(new
							{
								phase = "volume_node",
								subunit = num3,
								error = ex8.Message
							});
						}
						Marshal.Release(subunit);
					}
					catch (Exception ex9)
					{
						list.Add(new
						{
							phase = "subunit",
							index = num3,
							error = ex9.Message
						});
					}
				}
				Marshal.Release(pInterface2);
			}
			else
			{
				list.Add(new
				{
					phase = "topology",
					status = "Activate returned null"
				});
			}
		}
		catch (Exception ex10)
		{
			list.Add(new
			{
				phase = "topology_activate",
				error = ex10.Message
			});
		}
		Marshal.Release(device);
		return Json(new
		{
			results = list
		});
	}

	private static string DebugSessions(IMMDeviceEnumerator enumerator)
	{
		List<object> list = new List<object>();
		int stateMask = 11;
		enumerator.EnumAudioEndpoints(0, stateMask, out var devices);
		if (devices != IntPtr.Zero)
		{
			IMMDeviceCollection iMMDeviceCollection = (IMMDeviceCollection)Marshal.GetTypedObjectForIUnknown(devices, typeof(IMMDeviceCollection));
			iMMDeviceCollection.GetCount(out var count);
			for (int i = 0; i < count; i++)
			{
				iMMDeviceCollection.Item(i, out var device);
				IMMDevice iMMDevice = (IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice));
				iMMDevice.GetId(out var id);
				string deviceId = Marshal.PtrToStringUni(id) ?? "?";
				Marshal.FreeCoTaskMem(id);
				iMMDevice.GetState(out var state);
				string deviceName = GetDeviceName(iMMDevice);
				List<object> list2 = new List<object>();
				try
				{
					iMMDevice.Activate(ref IID_IAudioSessionManager2, 1, IntPtr.Zero, out var pInterface);
					((IAudioSessionManager2)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioSessionManager2))).GetSessionEnumerator(out var enumerator2);
					IAudioSessionEnumerator audioSessionEnumerator = (IAudioSessionEnumerator)Marshal.GetTypedObjectForIUnknown(enumerator2, typeof(IAudioSessionEnumerator));
					audioSessionEnumerator.GetCount(out var count2);
					for (int j = 0; j < count2; j++)
					{
						audioSessionEnumerator.GetSession(j, out var session);
						IAudioSessionControl2 audioSessionControl = (IAudioSessionControl2)Marshal.GetTypedObjectForIUnknown(session, typeof(IAudioSessionControl2));
						audioSessionControl.GetProcessId(out var pid);
						int state2 = audioSessionControl.GetState();
						string rawName = "?";
						try
						{
							rawName = audioSessionControl.GetDisplayName() ?? "(null)";
						}
						catch
						{
						}
						string iconPath = "?";
						try
						{
							iconPath = audioSessionControl.GetIconPath() ?? "(null)";
						}
						catch
						{
						}
						float level = -1f;
						try
						{
							((ISimpleAudioVolume)Marshal.GetTypedObjectForIUnknown(session, typeof(ISimpleAudioVolume))).GetMasterVolume(out level);
						}
						catch
						{
						}
						list2.Add(new
						{
							pid = pid,
							state = state2,
							rawName = rawName,
							iconPath = iconPath,
							volume = level
						});
						Marshal.Release(session);
					}
					Marshal.Release(enumerator2);
					Marshal.Release(pInterface);
				}
				catch (Exception ex)
				{
					list2.Add(new
					{
						error = ex.Message
					});
				}
				list.Add(new
				{
					deviceId = deviceId,
					deviceName = deviceName,
					deviceState = state,
					sessions = list2
				});
				Marshal.Release(device);
			}
			Marshal.Release(devices);
		}
		return Json(new
		{
			results = list
		});
	}

	private static string GetDeviceVolume(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			enumerator.GetDevice(cmd.id, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface);
			IAudioEndpointVolume obj = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
			obj.GetMasterVolumeLevelScalar(out var level);
			int mute = obj.GetMute();
			Marshal.Release(pInterface);
			Marshal.Release(device);
			return Json(new
			{
				volume = (int)(level * 100f),
				muted = (mute != 0),
				hasEndpointVolume = true
			});
		}
		catch
		{
			return Json(new
			{
				volume = 100,
				muted = false,
				hasEndpointVolume = false
			});
		}
	}

	private static string SetDeviceVolume(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			enumerator.GetDevice(cmd.id, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface);
			IAudioEndpointVolume obj = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
			Guid eventContext = Guid.Empty;
			obj.SetMasterVolumeLevelScalar(cmd.volume / 100f, ref eventContext);
			Marshal.Release(pInterface);
			Marshal.Release(device);
			return Json(new
			{
				success = true
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string SetDeviceMute(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			enumerator.GetDevice(cmd.id, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface);
			IAudioEndpointVolume obj = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
			Guid eventContext = Guid.Empty;
			obj.SetMute(cmd.mute ? 1 : 0, ref eventContext);
			Marshal.Release(pInterface);
			Marshal.Release(device);
			return Json(new
			{
				success = true
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string GetListen(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			enumerator.GetDevice(cmd.id, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).OpenPropertyStore(0, out var properties);
			IPropertyStore propertyStore = (IPropertyStore)Marshal.GetTypedObjectForIUnknown(properties, typeof(IPropertyStore));
			bool enabled = false;
			string playbackDeviceId = null;
			try
			{
				PropertyKey key = new PropertyKey(ListenPropertyGuid, 1);
				propertyStore.GetValue(ref key, out var value);
				enabled = value.vt == 11 && value.value != IntPtr.Zero;
			}
			catch
			{
			}
			try
			{
				PropertyKey key2 = new PropertyKey(ListenPropertyGuid, 0);
				propertyStore.GetValue(ref key2, out var value2);
				if (value2.vt == 31 && value2.value != IntPtr.Zero)
				{
					playbackDeviceId = Marshal.PtrToStringUni(value2.value);
				}
			}
			catch
			{
			}
			Marshal.Release(properties);
			Marshal.Release(device);
			return Json(new { enabled, playbackDeviceId });
		}
		catch
		{
			return Json(new
			{
				enabled = false,
				playbackDeviceId = (string)null,
				notSupported = true
			});
		}
	}

	private static string SetListen(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			enumerator.GetDevice(cmd.id, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).OpenPropertyStore(2, out var properties);
			IPropertyStore obj = (IPropertyStore)Marshal.GetTypedObjectForIUnknown(properties, typeof(IPropertyStore));
			PropertyKey key = new PropertyKey(ListenPropertyGuid, 0);
			PROPVARIANT value = PROPVARIANT.FromString(cmd.playbackDeviceId ?? "");
			obj.SetValue(ref key, ref value);
			PropertyKey key2 = new PropertyKey(ListenPropertyGuid, 1);
			PROPVARIANT value2 = PROPVARIANT.FromBool(cmd.enabled == true);
			obj.SetValue(ref key2, ref value2);
			Marshal.Release(properties);
			Marshal.Release(device);
			return Json(new
			{
				success = true
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string GetDeviceFormat(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			enumerator.GetDevice(cmd.id, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).OpenPropertyStore(0, out var properties);
			IPropertyStore obj = (IPropertyStore)Marshal.GetTypedObjectForIUnknown(properties, typeof(IPropertyStore));
			PropertyKey key = new PropertyKey(PKEY_AudioEngine_DeviceFormat, 0);
			PROPVARIANT value = default(PROPVARIANT);
			obj.GetValue(ref key, out value);
			if ((value.vt != 65 && value.vt != 4113) || value.blobData == IntPtr.Zero || value.blobSize < 16)
			{
				Marshal.Release(properties);
				Marshal.Release(device);
				return Json(new
				{
					error = "Device does not expose format property"
				});
			}
			WaveFormatExtensible waveFormatExtensible = Marshal.PtrToStructure<WaveFormatExtensible>(value.blobData);
			Marshal.Release(properties);
			Marshal.Release(device);
			return Json(new
			{
				sampleRate = waveFormatExtensible.nSamplesPerSec,
				bitDepth = waveFormatExtensible.wBitsPerSample,
				channels = waveFormatExtensible.nChannels,
				subType = ((waveFormatExtensible.SubFormat == KSDATAFORMAT_SUBTYPE_PCM) ? "PCM" : waveFormatExtensible.SubFormat.ToString())
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string SetDeviceFormat(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			enumerator.GetDevice(cmd.id, out var device);
			IMMDevice iMMDevice = (IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice));
			iMMDevice.OpenPropertyStore(0, out var properties);
			IPropertyStore obj = (IPropertyStore)Marshal.GetTypedObjectForIUnknown(properties, typeof(IPropertyStore));
			PropertyKey key = new PropertyKey(PKEY_AudioEngine_DeviceFormat, 0);
			PROPVARIANT value = default(PROPVARIANT);
			obj.GetValue(ref key, out value);
			if ((value.vt != 65 && value.vt != 4113) || value.blobData == IntPtr.Zero || value.blobSize < 16)
			{
				Marshal.Release(properties);
				Marshal.Release(device);
				return Json(new
				{
					error = "Device does not expose format property"
				});
			}
			byte[] array = new byte[value.blobSize];
			Marshal.Copy(value.blobData, array, 0, (int)value.blobSize);
			Marshal.Release(properties);
			GCHandle gCHandle = GCHandle.Alloc(array, GCHandleType.Pinned);
			WaveFormatExtensible structure = Marshal.PtrToStructure<WaveFormatExtensible>(gCHandle.AddrOfPinnedObject());
			int num = cmd.sampleRate ?? ((int)structure.nSamplesPerSec);
			int num2 = cmd.bitDepth ?? structure.wBitsPerSample;
			int num3 = cmd.channels ?? structure.nChannels;
			structure.nSamplesPerSec = (uint)num;
			structure.wBitsPerSample = (ushort)num2;
			structure.wValidBitsPerSample = (ushort)num2;
			structure.nChannels = (ushort)num3;
			structure.nBlockAlign = (ushort)(num3 * num2 / 8);
			structure.nAvgBytesPerSec = (uint)(num * num3 * num2 / 8);
			Marshal.StructureToPtr(structure, gCHandle.AddrOfPinnedObject(), fDeleteOld: false);
			gCHandle.Free();
			IPolicyConfig obj2 = (IPolicyConfig)new PolicyConfigClient();
			nint num4 = Marshal.AllocHGlobal(array.Length);
			Marshal.Copy(array, 0, num4, array.Length);
			obj2.SetDeviceFormat(cmd.id, num4, num4);
			Marshal.FreeHGlobal(num4);
			iMMDevice.OpenPropertyStore(2, out var properties2);
			IPropertyStore obj3 = (IPropertyStore)Marshal.GetTypedObjectForIUnknown(properties2, typeof(IPropertyStore));
			PROPVARIANT value2 = PROPVARIANT.FromBlob(array);
			obj3.SetValue(ref key, ref value2);
			PropertyKey key2 = new PropertyKey(PKEY_AudioEngine_OEMFormat, 3);
			obj3.SetValue(ref key2, ref value2);
			obj3.Commit();
			value2.FreeBlob();
			Marshal.Release(properties2);
			Marshal.Release(device);
			return Json(new
			{
				success = true
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static void EnsurePolicyConfig()
	{
		if (_policyConfigChecked)
		{
			return;
		}
		_policyConfigChecked = true;
		WindowsCreateString("Windows.Media.Internal.AudioPolicyConfig", (uint)"Windows.Media.Internal.AudioPolicyConfig".Length, out var hstring);
		try
		{
			nint factory;
			try
			{
				RoGetActivationFactory(hstring, ref IID_IAudioPolicyConfigFactory21H2, out factory);
			}
			catch
			{
				RoGetActivationFactory(hstring, ref IID_IAudioPolicyConfigFactory, out factory);
			}
			_policyConfigFactory = factory;
			nint num = Marshal.ReadIntPtr(factory);
			_setPersistedDefaultAudioEndpoint = (SetPersistedDefaultAudioEndpointDelegate)Marshal.GetDelegateForFunctionPointer(Marshal.ReadIntPtr(num + 25 * IntPtr.Size), typeof(SetPersistedDefaultAudioEndpointDelegate));
			_getPersistedDefaultAudioEndpoint = (GetPersistedDefaultAudioEndpointDelegate)Marshal.GetDelegateForFunctionPointer(Marshal.ReadIntPtr(num + 26 * IntPtr.Size), typeof(GetPersistedDefaultAudioEndpointDelegate));
			_policyConfigAvailable = true;
		}
		catch
		{
			_policyConfigAvailable = false;
		}
		finally
		{
			WindowsDeleteString(hstring);
		}
	}

	private static string ReadHString(nint hstring)
	{
		if (hstring == IntPtr.Zero)
		{
			return null;
		}
		string result = Marshal.PtrToStringUni(WindowsGetStringRawBuffer(hstring, out var length), (int)length);
		WindowsDeleteString(hstring);
		return result;
	}

	private static string PackDeviceId(string deviceId)
	{
		return "\\\\?\\SWD#MMDEVAPI#" + deviceId + "#{e6327cad-dcec-4949-ae8a-991e976a79d2}";
	}

	private static string UnpackDeviceId(string deviceId)
	{
		if (string.IsNullOrEmpty(deviceId))
		{
			return null;
		}
		if (deviceId.StartsWith("\\\\?\\SWD#MMDEVAPI#"))
		{
			deviceId = deviceId.Substring("\\\\?\\SWD#MMDEVAPI#".Length);
		}
		if (deviceId.EndsWith("#{e6327cad-dcec-4949-ae8a-991e976a79d2}"))
		{
			deviceId = deviceId.Substring(0, deviceId.Length - "#{e6327cad-dcec-4949-ae8a-991e976a79d2}".Length);
		}
		if (deviceId.EndsWith("#{2eef81be-33fa-4800-9670-1cd474972c3f}"))
		{
			deviceId = deviceId.Substring(0, deviceId.Length - "#{2eef81be-33fa-4800-9670-1cd474972c3f}".Length);
		}
		return deviceId;
	}

	private static string SetSessionDevice(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			EnsurePolicyConfig();
			if (!_policyConfigAvailable)
			{
				return Json(new
				{
					error = "此系统不支持应用音频路由（PolicyConfig不可用）"
				});
			}
			nint hstring = IntPtr.Zero;
			if (!string.IsNullOrEmpty(cmd.deviceId))
			{
				string text = PackDeviceId(cmd.deviceId);
				WindowsCreateString(text, (uint)text.Length, out hstring);
			}
			_setPersistedDefaultAudioEndpoint(_policyConfigFactory, cmd.pid, EDataFlow.eRender, ERole.eMultimedia, hstring);
			_setPersistedDefaultAudioEndpoint(_policyConfigFactory, cmd.pid, EDataFlow.eRender, ERole.eConsole, hstring);
			if (hstring != IntPtr.Zero)
			{
				WindowsDeleteString(hstring);
			}
			return Json(new
			{
				success = true
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string GetSessionDevice(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			EnsurePolicyConfig();
			if (!_policyConfigAvailable)
			{
				return Json(new
				{
					deviceId = (string)null
				});
			}
			int num = _getPersistedDefaultAudioEndpoint(_policyConfigFactory, cmd.pid, EDataFlow.eRender, ERole.eMultimedia, out var deviceId);
			string deviceId2 = null;
			if (num >= 0)
			{
				deviceId2 = ReadHString(deviceId);
			}
			return Json(new
			{
				deviceId = UnpackDeviceId(deviceId2)
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				deviceId = (string)null,
				error = ex.Message
			});
		}
	}

	private static string? GetDefaultDeviceId(IMMDeviceEnumerator enumerator, EDataFlow flow)
	{
		try
		{
			enumerator.GetDefaultAudioEndpoint((int)flow, 0, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).GetId(out var id);
			string? result = Marshal.PtrToStringUni(id);
			Marshal.FreeCoTaskMem(id);
			Marshal.Release(device);
			return result;
		}
		catch
		{
			return null;
		}
	}

	private static string SaveProfile(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			string name = cmd.name ?? "default";
			Directory.CreateDirectory(ProfileDir);
			ProfileData profileData = new ProfileData
			{
				Name = name,
				CreatedAt = DateTime.Now.ToString("o")
			};
			try
			{
				enumerator.GetDefaultAudioEndpoint(0, 0, out var device);
				((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface);
				IAudioEndpointVolume obj = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
				obj.GetMasterVolumeLevelScalar(out var level);
				int mute = obj.GetMute();
				profileData.MasterVolume = (int)(level * 100f);
				profileData.MasterMuted = mute != 0;
				Marshal.Release(pInterface);
				Marshal.Release(device);
			}
			catch
			{
			}
			profileData.DefaultRenderDeviceId = GetDefaultDeviceId(enumerator, EDataFlow.eRender);
			profileData.DefaultCaptureDeviceId = GetDefaultDeviceId(enumerator, EDataFlow.eCapture);
			profileData.DeviceVolumes = new Dictionary<string, ProfileDeviceVolume>();
			profileData.DeviceStates = new Dictionary<string, string>();
			EDataFlow[] array = new EDataFlow[2]
			{
				EDataFlow.eRender,
				EDataFlow.eCapture
			};
			foreach (EDataFlow dataFlow in array)
			{
				int stateMask = 11;
				enumerator.EnumAudioEndpoints((int)dataFlow, stateMask, out var devices);
				if (devices == IntPtr.Zero)
				{
					continue;
				}
				IMMDeviceCollection iMMDeviceCollection = (IMMDeviceCollection)Marshal.GetTypedObjectForIUnknown(devices, typeof(IMMDeviceCollection));
				iMMDeviceCollection.GetCount(out var count);
				for (int j = 0; j < count; j++)
				{
					iMMDeviceCollection.Item(j, out var device2);
					IMMDevice iMMDevice = (IMMDevice)Marshal.GetTypedObjectForIUnknown(device2, typeof(IMMDevice));
					iMMDevice.GetState(out var state);
					iMMDevice.GetId(out var id);
					string text = Marshal.PtrToStringUni(id) ?? "";
					Marshal.FreeCoTaskMem(id);
					Dictionary<string, string> deviceStates = profileData.DeviceStates;
					string key = text;
					deviceStates[key] = state switch
					{
						1 => "active", 
						2 => "disabled", 
						4 => "not-present", 
						8 => "unplugged", 
						_ => "unknown", 
					};
					if (state == 1)
					{
						try
						{
							iMMDevice.Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface2);
							IAudioEndpointVolume obj3 = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface2, typeof(IAudioEndpointVolume));
							obj3.GetMasterVolumeLevelScalar(out var level2);
							int mute2 = obj3.GetMute();
							profileData.DeviceVolumes[text] = new ProfileDeviceVolume((int)(level2 * 100f), mute2 != 0);
							Marshal.Release(pInterface2);
						}
						catch
						{
						}
					}
					Marshal.Release(device2);
				}
				Marshal.Release(devices);
			}
			profileData.SessionRouting = new Dictionary<uint, string>();
			profileData.SessionRoutingByProcess = new Dictionary<string, string>();
			try
			{
				SessionListResult sessionListResult = JsonSerializer.Deserialize<SessionListResult>(ListSessions(enumerator));
				if (sessionListResult?.sessions != null)
				{
					profileData.SessionVolumes = new Dictionary<uint, ProfileDeviceVolume>();
					foreach (SessionInfo session in sessionListResult.sessions)
					{
						if (!string.IsNullOrEmpty(session.deviceId))
						{
							profileData.SessionRouting[session.pid] = session.deviceId;
						}
						if (!string.IsNullOrEmpty(session.deviceId) && !string.IsNullOrEmpty(session.processName))
						{
							profileData.SessionRoutingByProcess[session.processName.ToLowerInvariant()] = session.deviceId;
						}
						profileData.SessionVolumes[session.pid] = new ProfileDeviceVolume(session.volume, session.muted);
					}
				}
			}
			catch
			{
			}
			string contents = JsonSerializer.Serialize(profileData, new JsonSerializerOptions
			{
				WriteIndented = true
			});
			string path = Path.Combine(ProfileDir, SanitizeFileName(name) + ".json");
			File.WriteAllText(path, contents);
			return Json(new
			{
				success = true,
				path = path
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string LoadProfile(IMMDeviceEnumerator enumerator, Command cmd)
	{
		try
		{
			string text = cmd.name ?? "default";
			string path = Path.Combine(ProfileDir, SanitizeFileName(text) + ".json");
			if (!File.Exists(path))
			{
				return Json(new
				{
					error = "配置文件不存在: " + text
				});
			}
			ProfileData profileData = JsonSerializer.Deserialize<ProfileData>(File.ReadAllText(path));
			if (profileData == null)
			{
				return Json(new
				{
					error = "配置文件损坏"
				});
			}
			List<string> list = new List<string>();
			if (profileData.DeviceStates != null)
			{
				try
				{
					IPolicyConfig policyConfig = (IPolicyConfig)new PolicyConfigClient();
					foreach (KeyValuePair<string, string> deviceState in profileData.DeviceStates)
					{
						try
						{
							bool flag = deviceState.Value == "active";
							policyConfig.SetEndpointVisibility(deviceState.Key, flag ? ((short)1) : ((short)0));
						}
						catch
						{
						}
					}
				}
				catch (Exception ex)
				{
					list.Add("设备状态恢复: " + ex.Message);
				}
			}
			if (profileData.MasterVolume.HasValue)
			{
				try
				{
					enumerator.GetDefaultAudioEndpoint(0, 0, out var device);
					((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface);
					IAudioEndpointVolume obj2 = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
					Guid eventContext = Guid.Empty;
					obj2.SetMasterVolumeLevelScalar((float)profileData.MasterVolume.Value / 100f, ref eventContext);
					obj2.SetMute((profileData.MasterMuted == true) ? 1 : 0, ref eventContext);
					Marshal.Release(pInterface);
					Marshal.Release(device);
				}
				catch (Exception ex2)
				{
					list.Add("主音量: " + ex2.Message);
				}
			}
			if (!string.IsNullOrEmpty(profileData.DefaultRenderDeviceId))
			{
				try
				{
					IPolicyConfig obj3 = (IPolicyConfig)new PolicyConfigClient();
					obj3.SetDefaultEndpoint(profileData.DefaultRenderDeviceId, ERole.eConsole);
					obj3.SetDefaultEndpoint(profileData.DefaultRenderDeviceId, ERole.eMultimedia);
					obj3.SetDefaultEndpoint(profileData.DefaultRenderDeviceId, ERole.eCommunications);
				}
				catch (Exception ex3)
				{
					list.Add("默认播放设备: " + ex3.Message);
				}
			}
			if (!string.IsNullOrEmpty(profileData.DefaultCaptureDeviceId))
			{
				try
				{
					IPolicyConfig obj4 = (IPolicyConfig)new PolicyConfigClient();
					obj4.SetDefaultEndpoint(profileData.DefaultCaptureDeviceId, ERole.eConsole);
					obj4.SetDefaultEndpoint(profileData.DefaultCaptureDeviceId, ERole.eMultimedia);
					obj4.SetDefaultEndpoint(profileData.DefaultCaptureDeviceId, ERole.eCommunications);
				}
				catch (Exception ex4)
				{
					list.Add("默认录制设备: " + ex4.Message);
				}
			}
			if (profileData.DeviceVolumes != null)
			{
				foreach (KeyValuePair<string, ProfileDeviceVolume> deviceVolume in profileData.DeviceVolumes)
				{
					try
					{
						enumerator.GetDevice(deviceVolume.Key, out var device2);
						((IMMDevice)Marshal.GetTypedObjectForIUnknown(device2, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface2);
						IAudioEndpointVolume obj5 = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface2, typeof(IAudioEndpointVolume));
						Guid eventContext2 = Guid.Empty;
						obj5.SetMasterVolumeLevelScalar((float)deviceVolume.Value.Volume / 100f, ref eventContext2);
						obj5.SetMute(deviceVolume.Value.Muted ? 1 : 0, ref eventContext2);
						Marshal.Release(pInterface2);
						Marshal.Release(device2);
					}
					catch
					{
					}
				}
			}
			if (profileData.SessionRouting != null)
			{
				EnsurePolicyConfig();
				if (_policyConfigAvailable)
				{
					foreach (KeyValuePair<uint, string> item in profileData.SessionRouting)
					{
						try
						{
							nint hstring = IntPtr.Zero;
							if (!string.IsNullOrEmpty(item.Value))
							{
								string text2 = PackDeviceId(item.Value);
								WindowsCreateString(text2, (uint)text2.Length, out hstring);
							}
							_setPersistedDefaultAudioEndpoint(_policyConfigFactory, item.Key, EDataFlow.eRender, ERole.eMultimedia, hstring);
							_setPersistedDefaultAudioEndpoint(_policyConfigFactory, item.Key, EDataFlow.eRender, ERole.eConsole, hstring);
							if (hstring != IntPtr.Zero)
							{
								WindowsDeleteString(hstring);
							}
						}
						catch
						{
						}
					}
				}
			}
			if (profileData.SessionRoutingByProcess != null && profileData.SessionRoutingByProcess.Count > 0)
			{
				EnsurePolicyConfig();
				if (_policyConfigAvailable)
				{
					try
					{
						SessionListResult sessionListResult = JsonSerializer.Deserialize<SessionListResult>(ListSessions(enumerator));
						if (sessionListResult?.sessions != null)
						{
							Dictionary<string, uint> dictionary = new Dictionary<string, uint>();
							foreach (SessionInfo session in sessionListResult.sessions)
							{
								if (!string.IsNullOrEmpty(session.processName))
								{
									string key = session.processName.ToLowerInvariant();
									if (!dictionary.ContainsKey(key))
									{
										dictionary[key] = session.pid;
									}
								}
							}
							foreach (KeyValuePair<string, string> item2 in profileData.SessionRoutingByProcess)
							{
								if (string.IsNullOrEmpty(item2.Key))
								{
									continue;
								}
								string key2 = item2.Key.ToLowerInvariant();
								if (!dictionary.TryGetValue(key2, out var value))
								{
									continue;
								}
								try
								{
									nint hstring2 = IntPtr.Zero;
									if (!string.IsNullOrEmpty(item2.Value))
									{
										string text3 = PackDeviceId(item2.Value);
										WindowsCreateString(text3, (uint)text3.Length, out hstring2);
									}
									_setPersistedDefaultAudioEndpoint(_policyConfigFactory, value, EDataFlow.eRender, ERole.eMultimedia, hstring2);
									_setPersistedDefaultAudioEndpoint(_policyConfigFactory, value, EDataFlow.eRender, ERole.eConsole, hstring2);
									if (hstring2 != IntPtr.Zero)
									{
										WindowsDeleteString(hstring2);
									}
								}
								catch
								{
								}
							}
						}
					}
					catch
					{
					}
				}
			}
			if (profileData.SessionVolumes != null)
			{
				foreach (KeyValuePair<uint, ProfileDeviceVolume> sessionVolume in profileData.SessionVolumes)
				{
					try
					{
						foreach (ISimpleAudioVolume item3 in FindAllSessionVolumes(enumerator, sessionVolume.Key))
						{
							item3.SetMasterVolume((float)sessionVolume.Value.Volume / 100f, IntPtr.Zero);
							item3.SetMute(sessionVolume.Value.Muted ? 1 : 0, IntPtr.Zero);
						}
					}
					catch
					{
					}
				}
			}
			return Json(new
			{
				success = true,
				errors = ((list.Count > 0) ? list : null)
			});
		}
		catch (Exception ex5)
		{
			return Json(new
			{
				error = ex5.Message
			});
		}
	}

	private static string ListProfiles(IMMDeviceEnumerator _)
	{
		try
		{
			Directory.CreateDirectory(ProfileDir);
			string[] files = Directory.GetFiles(ProfileDir, "*.json");
			List<ProfileListItem> list = new List<ProfileListItem>();
			string[] array = files;
			foreach (string path in array)
			{
				try
				{
					ProfileData profileData = JsonSerializer.Deserialize<ProfileData>(File.ReadAllText(path));
					list.Add(new ProfileListItem(profileData?.Name ?? Path.GetFileNameWithoutExtension(path), profileData?.CreatedAt ?? "", Path.GetFileNameWithoutExtension(path)));
				}
				catch
				{
				}
			}
			return Json(new
			{
				profiles = list
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string DeleteProfile(IMMDeviceEnumerator _, Command cmd)
	{
		try
		{
			string text = cmd.name ?? "default";
			string path = Path.Combine(ProfileDir, SanitizeFileName(text) + ".json");
			if (File.Exists(path))
			{
				File.Delete(path);
				return Json(new
				{
					success = true
				});
			}
			return Json(new
			{
				error = "配置文件不存在: " + text
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string ExportProfile(IMMDeviceEnumerator _, Command cmd)
	{
		try
		{
			string text = cmd.name ?? "default";
			string text2 = Path.Combine(ProfileDir, SanitizeFileName(text) + ".json");
			string destPath = cmd.destPath;
			if (!File.Exists(text2))
			{
				return Json(new
				{
					error = "配置文件不存在: " + text
				});
			}
			if (string.IsNullOrEmpty(destPath))
			{
				return Json(new
				{
					error = "未指定目标路径"
				});
			}
			File.Copy(text2, destPath, overwrite: true);
			return Json(new
			{
				success = true
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string ImportProfile(IMMDeviceEnumerator _, Command cmd)
	{
		try
		{
			string sourcePath = cmd.sourcePath;
			if (string.IsNullOrEmpty(sourcePath) || !File.Exists(sourcePath))
			{
				return Json(new
				{
					error = "源文件不存在"
				});
			}
			ProfileData profileData = JsonSerializer.Deserialize<ProfileData>(File.ReadAllText(sourcePath));
			if (profileData == null || string.IsNullOrEmpty(profileData.Name))
			{
				return Json(new
				{
					error = "无效的配置文件格式"
				});
			}
			Directory.CreateDirectory(ProfileDir);
			string destFileName = Path.Combine(ProfileDir, SanitizeFileName(profileData.Name) + ".json");
			File.Copy(sourcePath, destFileName, overwrite: true);
			return Json(new
			{
				success = true,
				name = profileData.Name
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string SetDeviceEnabled(IMMDeviceEnumerator _, Command cmd)
	{
		try
		{
			((IPolicyConfig)new PolicyConfigClient()).SetEndpointVisibility(cmd.id, (cmd.enabled == true) ? ((short)1) : ((short)0));
			return Json(new
			{
				success = true
			});
		}
		catch (Exception ex)
		{
			return Json(new
			{
				error = ex.Message
			});
		}
	}

	private static string MaxAllVolumes(IMMDeviceEnumerator enumerator)
	{
		List<string> list = new List<string>();
		Guid eventContext = Guid.Empty;
		try
		{
			enumerator.GetDefaultAudioEndpoint(0, 0, out var device);
			((IMMDevice)Marshal.GetTypedObjectForIUnknown(device, typeof(IMMDevice))).Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface);
			IAudioEndpointVolume obj = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface, typeof(IAudioEndpointVolume));
			obj.SetMasterVolumeLevelScalar(1f, ref eventContext);
			obj.SetMute(0, ref eventContext);
			Marshal.Release(pInterface);
			Marshal.Release(device);
			list.Add("主音量: 100");
		}
		catch (Exception ex)
		{
			list.Add("主音量失败: " + ex.Message);
		}
		EDataFlow[] array = new EDataFlow[2]
		{
			EDataFlow.eRender,
			EDataFlow.eCapture
		};
		foreach (EDataFlow dataFlow in array)
		{
			int stateMask = 11;
			enumerator.EnumAudioEndpoints((int)dataFlow, stateMask, out var devices);
			if (devices == IntPtr.Zero)
			{
				continue;
			}
			IMMDeviceCollection iMMDeviceCollection = (IMMDeviceCollection)Marshal.GetTypedObjectForIUnknown(devices, typeof(IMMDeviceCollection));
			iMMDeviceCollection.GetCount(out var count);
			for (int j = 0; j < count; j++)
			{
				iMMDeviceCollection.Item(j, out var device2);
				IMMDevice iMMDevice = (IMMDevice)Marshal.GetTypedObjectForIUnknown(device2, typeof(IMMDevice));
				iMMDevice.GetState(out var state);
				if (state == 1)
				{
					try
					{
						iMMDevice.Activate(ref IID_IAudioEndpointVolume, 1, IntPtr.Zero, out var pInterface2);
						IAudioEndpointVolume obj2 = (IAudioEndpointVolume)Marshal.GetTypedObjectForIUnknown(pInterface2, typeof(IAudioEndpointVolume));
						obj2.SetMasterVolumeLevelScalar(1f, ref eventContext);
						obj2.SetMute(0, ref eventContext);
						Marshal.Release(pInterface2);
					}
					catch
					{
					}
				}
				Marshal.Release(device2);
			}
			Marshal.Release(devices);
		}
		list.Add("所有设备: 100");
		try
		{
			int stateMask2 = 11;
			enumerator.EnumAudioEndpoints(0, stateMask2, out var devices2);
			if (devices2 != IntPtr.Zero)
			{
				IMMDeviceCollection iMMDeviceCollection2 = (IMMDeviceCollection)Marshal.GetTypedObjectForIUnknown(devices2, typeof(IMMDeviceCollection));
				iMMDeviceCollection2.GetCount(out var count2);
				for (int k = 0; k < count2; k++)
				{
					iMMDeviceCollection2.Item(k, out var device3);
					IMMDevice iMMDevice2 = (IMMDevice)Marshal.GetTypedObjectForIUnknown(device3, typeof(IMMDevice));
					iMMDevice2.GetState(out var state2);
					if (state2 != 1)
					{
						Marshal.Release(device3);
						continue;
					}
					try
					{
						iMMDevice2.Activate(ref IID_IAudioSessionManager2, 1, IntPtr.Zero, out var pInterface3);
						((IAudioSessionManager2)Marshal.GetTypedObjectForIUnknown(pInterface3, typeof(IAudioSessionManager2))).GetSessionEnumerator(out var enumerator2);
						IAudioSessionEnumerator audioSessionEnumerator = (IAudioSessionEnumerator)Marshal.GetTypedObjectForIUnknown(enumerator2, typeof(IAudioSessionEnumerator));
						audioSessionEnumerator.GetCount(out var count3);
						for (int l = 0; l < count3; l++)
						{
							audioSessionEnumerator.GetSession(l, out var session);
							try
							{
								ISimpleAudioVolume obj4 = (ISimpleAudioVolume)Marshal.GetTypedObjectForIUnknown(session, typeof(ISimpleAudioVolume));
								obj4.SetMasterVolume(1f, IntPtr.Zero);
								obj4.SetMute(0, IntPtr.Zero);
							}
							catch
							{
							}
							Marshal.Release(session);
						}
						Marshal.Release(enumerator2);
						Marshal.Release(pInterface3);
					}
					catch
					{
					}
					Marshal.Release(device3);
				}
				Marshal.Release(devices2);
			}
			list.Add("所有应用程序: 100");
		}
		catch (Exception ex2)
		{
			list.Add("应用程序音量: " + ex2.Message);
		}
		return Json(new
		{
			success = true,
			results = list
		});
	}

	private static string SanitizeFileName(string name)
	{
		char[] invalidFileNameChars = Path.GetInvalidFileNameChars();
		char[] array = name.ToCharArray();
		for (int i = 0; i < array.Length; i++)
		{
			if (Enumerable.Contains(invalidFileNameChars, array[i]))
			{
				array[i] = '_';
			}
		}
		return new string(array);
	}
}
