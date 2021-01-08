//PipetteController.cs ==> findSurface
public FloErrorCode FindSurface(uint index, LldMode mode, double lowestTargetPos, out double surfacePos)
{
    FloErrorCode errorCode;

    switch (mode)
    {
        case LldMode.Resistance:
            errorCode = _wlld.FindSurface(index, lowestTargetPos, out surfacePos);
            break;
        case LldMode.Pressure:
            errorCode = _plld.FindSurface(index, lowestTargetPos, out surfacePos);
			// findsurface @ PressureLLD.cs
			public class PressureLld : ISurfaceDetector
			{
				private readonly PipetteModel _pipette;
				private readonly FirmwareLoggerService _firmwareLogger;
				private readonly PipetteAbortConfig[] _stemHardBrakeConfigs;
				private readonly PipetteAbortConfig[] _stemNormalConfigs;
				private readonly PipetteAbortConfig[] _valvInConfigs;
				private readonly PlldConfig[] _plldConfigs;
				private readonly FirmwareLogConfig[] _firmwareLogConfigs;
				private readonly double[] _collisionCompressionTolerances;
				private readonly ILogger _logger;

				public PressureLld(PipetteModel pipette, FirmwareLoggerService firmwareLogger, PipetteAbortConfig[] stemHardBrakeConfigs, PipetteAbortConfig[] stemNormalConfigs, PipetteAbortConfig[] valveInConfigs,
					PlldConfig[] plldConfig, double[] collisionCompressionTolerance, FirmwareLogConfig[] firmwareLogConfig, ILogger logger)
				{
					_pipette = pipette;
					_firmwareLogger = firmwareLogger;
					_stemHardBrakeConfigs = stemHardBrakeConfigs;
					_stemNormalConfigs = stemNormalConfigs;
					_valvInConfigs = valveInConfigs;
					_plldConfigs = plldConfig;
					_collisionCompressionTolerances = collisionCompressionTolerance;
					_firmwareLogConfigs = firmwareLogConfig;
					_logger = logger;
				}

				public FloErrorCode FindSurface(uint index, double lowestTargetPosition, out double surfacePos)
				{
					if (_pipette.IsSimulated(index))
						//IsSimulated @ pipetteModel.cs
						public bool IsSimulated(uint index)
						{
							return _pipetteService.IsSimulated(index);
							//isSimulated @ pipetteService.cs
							public bool IsSimulated(uint index)
							{
								if (_stemActuators[index] is SimActuator)
									return true;
								else
									return false;
							}
						}
					{
						_logger.LogDebug($"Pip{index},FindSurface,simulated");
						surfacePos = 0;
						return FloErrorCode.NoError;
					}

					_firmwareLogger.Start(index, _firmwareLogConfigs[index].StemMotorMask, _firmwareLogConfigs[index].SensorMask, FirmwareLoggerService.BuildHeaderMessage(_firmwareLogConfigs[index].HeaderMessage, _firmwareLogConfigs[index].HeaderMessageDateFormat));
					lowestTargetPosition -= _collisionCompressionTolerances[index]; //add with spring z tolerance
					_logger.LogDebug($"Pip{index},FindSurface,start,lowestPos{lowestTargetPosition}");
					//_pipette.StartRegulatorFlow( index, _plldConfigs[index].Flow );
					//Thread.Sleep( _plldConfigs[index].SetFlowDelay );
					_pipette.StartRegulatorMode(index, FlowRegulatorMode.FlowCheck, _plldConfigs[index].Flow, RegulatorPIDMode.Dispense);
						//startRegulatorMode @ pipetteModel.cs
						public PipettingStatus StartRegulatorMode(uint index, FlowRegulatorMode mode, double target, RegulatorPIDMode pidSelect, bool activeDPCVolumeLimit = false, double volumeLimit = 0)
						{
							_logger.LogDebug($"Pip{index},StartRegulatorMode,mode={mode},target={target},PIDSelect={pidSelect},activeDPCVolumeLimit={activeDPCVolumeLimit},volumeLimit={volumeLimit},start");

							if (_lastPipettingError[index] == FloErrorCode.PipettingInvalidPressure)
								return PipettingStatus.InvalidPressure;

							_pipetteService.SetValveOpenResponseMs(index, _valveConfig.NonPipettingResponseMs);

							PipettingStatus status = _pipetteService.StartRegulatorMode(index, mode, target, pidSelect, activeDPCVolumeLimit, volumeLimit);
							// StartRegulatorMode goes to pipetteservice.cs -> iflowpipetteregulator.cs -> ipipetteregulatorboard.cs -> firmware
							_logger.LogDebug($"Pip{index},StartRegulatorMode,status={status},end");
							return status;
						}
					_pipette.SetAd9833Frequency(index, _plldConfigs[index].Ad9833Frequency);
					Thread.Sleep(_plldConfigs[index].SetFrequencyDelay);
					double threshold = FindThreshold(index);
					// FindThresshold @ PressureLLD.cs
					private double FindThreshold(uint index)
					{
						// Open Flow and averaging
						_pipette.SetSensorAveragingWindowSize(index, (short)AverageWindowId.Pressure1, _plldConfigs[index].WindowSize);
						_pipette.SetSensorAveragingWindowSize(index, (short)AverageWindowId.Pressure2, _plldConfigs[index].WindowSize);

						// P reff
						_pipette.AveragingPressure(index, _plldConfigs[index].PressureAveragingSample);
						_pipette.WaitAveragingDone(index);
						double pref = _pipette.GetPressureRef(index);
						_logger.LogDebug($"Pip{index},pRef={pref}");
						double threshold;

						if (_plldConfigs[index].UseDynamicThreshold)
						{
							_pipette.GetPressureMinMax(index, out double minP1, out double maxP1, out double minP2, out double maxP2);
							threshold = ((maxP2 - minP2) / 2) * _plldConfigs[index].AbortPressureThreshold;
						}
						else
						{
							threshold = _plldConfigs[index].AbortPressureThreshold;
						}
						return pref + threshold;
						ClearStemNormalAbort(index);
						// ClearStemNormalAbort @ PressureLLD.cs
						private void ClearStemNormalAbort(uint index)
						{
							_stemNormalConfigs[index].Init();
							_pipette.SetAbortConfig(index, _stemNormalConfigs[index]);
							_stemNormalConfigs[index].AbortInputFlag.AbortOnTipCollision2 = false;
							_stemNormalConfigs[index].AbortInputFlag.AbortOnStemCurrent = false;
							_stemNormalConfigs[index].AbortInputFlag.AbortOnSyringePressure2 = false;
							_pipette.ClearTriggeredInputs(index, PipetteAbortType.PipetteStemNormal);
						}
						_pipette.ClearZHardBrakeAbortConfigAndFaults(index);
						// ClearZHardBrakeAbortCOnfigAndFaults @ pipetteModel.cs
						public FloErrorCode ClearZHardBrakeAbortConfigAndFaults(uint index)
						{
							_logger.LogDebug($"Pip{index},ClearZHardBrakeAbortConfigAndFaults,start");
							_pipetteAborts[PipetteAbortType.PipetteStemHardbrake][index].Init();
							SetAbortConfig(index, _pipetteAborts[PipetteAbortType.PipetteStemHardbrake][index]);
							FloErrorCode errCode = ClearTriggeredInputs(index, PipetteAbortType.PipetteStemHardbrake);
							if (errCode != FloErrorCode.NoError) return errCode;

							_logger.LogDebug($"Pip{index},ClearZHardBrakeAbortConfigAndFaults,end");
							return ClearFaults(index);
						}
						ClearValveInAbort(index);
						private void ClearValveInAbort(uint index)
						{
							_valvInConfigs[index].AbortInputFlag.AbortOnTipCollision2 = false;
							_valvInConfigs[index].AbortInputFlag.AbortOnStemCurrent = false;
							_valvInConfigs[index].AbortInputFlag.AbortOnSyringePressure2 = false;
							_pipette.SetAbortConfig(index, _valvInConfigs[index]);
							_pipette.ClearTriggeredInputs(index, PipetteAbortType.ValveIn);
						}
						SetAbortPlld(index, threshold);
						// SetAbortPLLD @ PressureLLD.cs
						{
							_pipette.SetAbortThreshold(index, AbortAnalogInput.CollisionSensor2, _pipette.ReadAnalogSensor(index, AnalogSensor.Collision) - _plldConfigs[index].AbortCollisionThreshold);
							_pipette.SetAbortThreshold(index, AbortAnalogInput.PressureSensor2, threshold);
							_pipette.SetAbortThreshold(index, AbortAnalogInput.StemCurrentSensor, _plldConfigs[index].CurrentSensorThreshold);
							_pipette.SetAbortThreshold(index, AbortAnalogInput.LiquidLevelSensor, _pipette.ReadAnalogSensor(index, AnalogSensor.Dllt) - _plldConfigs[index].AbortResistanceThreshold);

							_stemNormalConfigs[index].AbortDelay = 0;
							_stemNormalConfigs[index].TriggerOnAll = false;
							_stemNormalConfigs[index].AbortInputFlag.AbortOnTipCollision2 = true;
							_stemNormalConfigs[index].AbortInputFlag.AbortOnStemCurrent = true;
							_stemNormalConfigs[index].AbortInputFlag.AbortOnSyringePressure2 = true;
							_pipette.SetAbortConfig(index, _stemNormalConfigs[index]);

							_stemHardBrakeConfigs[index].AbortDelay = 0;
							_stemHardBrakeConfigs[index].TriggerOnAll = false;
							_stemHardBrakeConfigs[index].AbortInputFlag.AbortOnTipCollision2 = true;
							_stemHardBrakeConfigs[index].AbortInputFlag.AbortOnStemCurrent = true;
							_stemHardBrakeConfigs[index].AbortInputFlag.AbortOnLiquidLevelSensor = true;
							_pipette.SetAbortConfig(index, _stemHardBrakeConfigs[index]);

							_valvInConfigs[index].AbortDelay = 0;
							_valvInConfigs[index].TriggerOnAll = false;
							_stemHardBrakeConfigs[index].AbortInputFlag.AbortOnTipCollision2 = true;
							_stemHardBrakeConfigs[index].AbortInputFlag.AbortOnStemCurrent = true;
							_valvInConfigs[index].AbortInputFlag.AbortOnSyringePressure2 = true;
							_pipette.SetAbortConfig(index, _valvInConfigs[index]);
						}

						FloErrorCode errCode = _pipette.Move(index, lowestTargetPosition, _plldConfigs[index].StemVel, _plldConfigs[index].StemAccel);

						if (errCode == FloErrorCode.NoError)
						{
							_pipette.WaitEOM(index);
						}

						_pipette.StopPipetting(index);
						{ //stopPipetting @ ppetteModel.cs
							FloErrorCode errorCode = _pipetteService.AbortFlowFunc(index).ToFloErrorCode();
							_tareDone[index].Set();
							_calibrateDone[index].Set();
							_countVolumeDone[index].Set();
							_averagingDone[index].Set();
							_pipettingDone[index].Set();
						}
						var abortFlagNormal = _pipette.GetTriggeredInputs(index, PipetteAbortType.PipetteStemNormal);
						var abortFlagHardBrake = _pipette.GetTriggeredInputs(index, PipetteAbortType.PipetteStemHardbrake);

						if (abortFlagNormal.AbortOnTipCollision2 || abortFlagHardBrake.AbortOnTipCollision2)
						{
							//dry dispense possible
							_logger.LogWarning($"Pip,{index},FindSurface,collision detected");
							errCode = FloErrorCode.CollisionTriggered;
						}
						else if (abortFlagHardBrake.AbortOnLiquidLevelSensor)
						{
							//liquid surface found
							double triggeredPos = _pipette.GetTriggeredPositions(index, PipetteAbortType.PipetteStemHardbrake).OnLiquidLevel;
							_logger.LogDebug($"Pip{index},FindSurface,liquid surface found,triggeredPos={triggeredPos},Resistance={_pipette.GetTriggeredValue(index, PipetteAbortType.PipetteStemHardbrake, PipetteAbortInputBitMasks.LiquidLevelSensor)}");
							errCode = FloErrorCode.NoError;
						}
						else if (abortFlagNormal.AbortOnSyringePressure2)
						{
							//liquid surface found
							double triggeredPos = _pipette.GetTriggeredPositions(index, PipetteAbortType.PipetteStemNormal).OnSyringePressure2;
							_logger.LogDebug($"Pip{index},FindSurface,liquid surface found,triggeredPos={triggeredPos},Pressure={_pipette.GetTriggeredValue(index, PipetteAbortType.PipetteStemNormal, PipetteAbortInputBitMasks.Pressure2)}");
							errCode = FloErrorCode.NoError;
						}
						else if (abortFlagNormal.AbortOnStemCurrent || abortFlagHardBrake.AbortOnStemCurrent)
						{
							_logger.LogWarning($"Pip{index},FindSurface,stem over current");
							errCode = FloErrorCode.OverCurrent;
						}
						else
						{
							_logger.LogWarning($"Pip{index},FindSurface,travel limit reached");
							errCode = FloErrorCode.TravelLimitReached;
						}

						_firmwareLogger.StopAndSaveToFile(index, FirmwareLoggerService.BuildHeaderMessage(_firmwareLogConfigs[index].FileName, _firmwareLogConfigs[index].FileNameDateFormat));
						ClearStemNormalAbort(index);
						_pipette.ClearZHardBrakeAbortConfigAndFaults(index);
						ClearValveInAbort(index);
						_pipette.GetPos(index, out surfacePos);
						_logger.LogDebug($"Pip{index},FindSurface,end,surface Pos={surfacePos},errorCode={errCode}");
						return errCode;
					}
				}
			}
            break;
        case LldMode.Collision:
            errorCode = _collisionLld.FindSurface(index, lowestTargetPos, out surfacePos);
            break;
        default:
            errorCode = FloErrorCode.UnknownError;
            surfacePos = -1;
            break;
    }

    return errorCode;
}