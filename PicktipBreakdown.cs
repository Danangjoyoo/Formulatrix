using System;
using System.Threading;
using Formulatrix.Flo.Device.GrpcApi;
using Formulatrix.Flo.Device.Controller.ConfigDefs;
using Microsoft.Extensions.Logging;
using Formulatrix.Rpc.Client.Firmware.FloEnum;
using Formulatrix.Flo.Labware;
using System.Collections.Generic;

namespace Formulatrix.Flo.Device.Controller
{
    public class PickTip
    {
        private readonly PipetteModel _pipette;
        private readonly PickTipConfig[] _pickTipConfigs;
        private readonly TipValidationConfig[] _tipValidationConfigs;
        private readonly PipetteAbortConfig[] _stemHardBrakeConfig;
        private readonly double[] _collisionCompressionTolerances;
        private readonly ILogger _logger;

        /// <summary>
        /// Validation results. False means failed
        /// </summary>
        private readonly bool[] _pressure2ValidationResults;
        private readonly bool[] _correctTipTypeResults;
        private readonly bool[] _collisionValidationResults;
        private readonly double[] _initialResistanceValues;
        private readonly double[] _atmPressureValues;
        private readonly bool[] _resistanceValidationResults;
        private readonly double[] _positionsBeforePickTip;
        private readonly double[] _targetRetractPos;

        private Dictionary<TipKey, ValidPressureLimit[]> _tipKeyValidPressureLimits;

        public PickTip(PipetteModel pipette, PickTipConfig[] pickTipConfigs, TipValidationConfig[] tipValidationConfigs,
            PipetteAbortConfig[] stemHardBrakeConfig, double[] collisionCompressionTolerances, ILogger logger)
        {
            _pipette = pipette;
            _pickTipConfigs = pickTipConfigs;
            _tipValidationConfigs = tipValidationConfigs;
            _stemHardBrakeConfig = stemHardBrakeConfig;
            _collisionCompressionTolerances = collisionCompressionTolerances;
            _logger = logger;

            _pressure2ValidationResults = new bool[_pickTipConfigs.Length];
            _correctTipTypeResults = new bool[_pickTipConfigs.Length];
            _collisionValidationResults = new bool[_pickTipConfigs.Length];
            _initialResistanceValues = new double[_pickTipConfigs.Length];
            _atmPressureValues = new double[_pickTipConfigs.Length];
            _resistanceValidationResults = new bool[_pickTipConfigs.Length];
            _positionsBeforePickTip = new double[_pickTipConfigs.Length];
            _targetRetractPos = new double[_pickTipConfigs.Length];

            _tipKeyValidPressureLimits = new Dictionary<TipKey, ValidPressureLimit[]>();
            for (int i = 0; i < _tipValidationConfigs.Length; i++)
            {
                ValidPressureLimit[] validPressureLimits = _tipValidationConfigs[i].ValidPressureLimit;
                for (int j = 0; j < validPressureLimits.Length; j++)
                {
                    TipKey tipKey = new TipKey(validPressureLimits[j].TipCapacity, validPressureLimits[j].TipType);
                    if (!_tipKeyValidPressureLimits.ContainsKey(tipKey))
                    {
                        _tipKeyValidPressureLimits.Add(tipKey, new ValidPressureLimit[_tipValidationConfigs.Length]);
                        _tipKeyValidPressureLimits[tipKey][i] = validPressureLimits[j];
                    }
                    else
                    {
                        _tipKeyValidPressureLimits[tipKey][i] = validPressureLimits[j];
                    }
                }
            }
        }

        public FloErrorCode Execute(uint index, double targetPos, TipCapacity tipCapacity, ref TipType tipType, double expectedTriggeredPos, bool retry, bool isGroup)
        {
            _logger.LogDebug($"Pip{index},Execute,targetPos={targetPos},tipCapacity={tipCapacity},tipType={tipType},expectedTriggeredPos={expectedTriggeredPos},retry={retry},isGroup={isGroup},start");

            if (_pipette.IsSimulated(index))
            {
                _logger.LogDebug($"Pip{index},Execute,end,simulated");
                return FloErrorCode.NoError;
            }

            _pipette.GetFolErrorConfig(index, out bool folErrorEnabled, out double folErrorLimit);
                // FW
                [Opcode(82)]
                GetFolErrorConfigResponse GetFolErrorConfig(short motorId);
            _pipette.SetFolErrorConfig(index, folErrorEnabled, _pickTipConfigs[index].FolErrorLimit);
                // FW
                [Opcode(83)]
                void SetFolErrorConfig(short motorId, bool isTrackingEnabled, double maxFolError);

            _logger.LogDebug($"Pip{index},Execute,SetFolErrorConfig,isEnable={folErrorEnabled} value={_pickTipConfigs[index].FolErrorLimit}");

            _pipette.GetTargetReachedParams(index, out double trackingWindow, out ushort trackingTimeMs);
                // FW
                [Opcode(86)]
                GetTargetReachedParamsResponse GetTargetReachedParams(short motorId);
            _pipette.SetTargetReachedParams(index, _pickTipConfigs[index].TargetReachedWindow, trackingTimeMs);
                //FW
                [Opcode(87)]
                void SetTargetReachedParams(short motorId, double trackingWindow, ushort trackingTimeMs);


            _logger.LogDebug($"Pip{index},Execute,SetTargetReachedParams,trackingWindow={_pickTipConfigs[index].TargetReachedWindow},trackingTimeMs={trackingTimeMs}");

            if (!retry)
            {
                _positionsBeforePickTip[index] = _pipette.LastKnownPos[index];
            }

            FloErrorCode errorCode = _pipette.StartRegulatorMode(index, FlowRegulatorMode.FlowCheck, _pickTipConfigs[index].Flow, RegulatorPIDMode.Dispense).ToFloErrorCode();
                // FW
                [Opcode(201)]
                ushort StartRegulatorMode(ushort mode, double target, ushort pidSelect, bool activeDPCVolumeLimit, double volumeLimit);

            if (errorCode == FloErrorCode.PipettingInvalidPressure)
            {
                _logger.LogDebug($"Pip{index},Execute,targetPos={targetPos},tipCapacity={tipCapacity},tipType={tipType},expectedTriggeredPos={expectedTriggeredPos},retry={retry},isGroup={isGroup},end,return={errorCode}");
                return errorCode;
            }

            if (!isGroup)
            {
                ReadInitialSensor(index);
                    public void ReadInitialSensor(uint index)
                    {
                        _logger.LogDebug($"Pip{index},ReadInitialSensor,start");

                        _initialResistanceValues[index] = 0;
                        _atmPressureValues[index] = _pipette.GetAtmPressure(index);

                        for (int i = 0; i < _tipValidationConfigs[index].ValidationSampleNum; i++)
                        {
                            _initialResistanceValues[index] += _pipette.ReadAnalogSensor(index, AnalogSensor.Dllt);
                            Thread.Sleep(_tipValidationConfigs[index].ValidationSamplingDelay);
                        }
                        _initialResistanceValues[index] /= _tipValidationConfigs[index].ValidationSampleNum;

                        _logger.LogDebug($"Pip{index},ReadInitialSensor,end,resistance={_initialResistanceValues[index]},atmPressure={_atmPressureValues[index]}");
                    }

            }

            targetPos -= _collisionCompressionTolerances[index];
            errorCode = PickTipFirstMove(index, targetPos, expectedTriggeredPos);
                private FloErrorCode PickTipFirstMove(uint index, double targetPos, double expectedTriggeredPos)
                {
                    _logger.LogDebug($"Pip{index},PickTipFirstMove,targetPos={targetPos},expectedTriggeredPos={expectedTriggeredPos},start");
                    FloErrorCode errCode;

                    //make stem hard brake if collision sensor or current sensor reading exceed limit
                    double collisionTreshold = _pipette.ReadAnalogSensor(index, AnalogSensor.Collision) - _pickTipConfigs[index].AbortCollisionThreshold;
                    _pipette.SetAbortThreshold(index, AbortAnalogInput.CollisionSensor2, collisionTreshold);
                    _pipette.SetAbortThreshold(index, AbortAnalogInput.StemCurrentSensor, _pickTipConfigs[index].FirstCurrentSensorThreshold);
                    _stemHardBrakeConfig[index].AbortInputFlag.AbortOnTipCollision2 = true;
                    _stemHardBrakeConfig[index].AbortInputFlag.AbortOnStemCurrent = true;
                    _pipette.SetAbortConfig(index, _stemHardBrakeConfig[index]);

                    errCode = _pipette.Move(index, targetPos, _pickTipConfigs[index].FirstMoveStemSpeed, _pickTipConfigs[index].FirstMoveStemAccel);
                    if (errCode != FloErrorCode.NoError)
                    {
                        _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                        _logger.LogDebug($"Pip{index},PickTipFirstMove,end,return={errCode}");
                        return errCode;
                    }

                    errCode = _pipette.WaitEOM(index);
                    if (errCode != FloErrorCode.NoError)
                    {
                        _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                        _logger.LogDebug($"Pip{index},PickTipFirstMove,end,return={errCode}");
                        return errCode;
                    }

                    var abortFlag = _pipette.GetTriggeredInputs(index, PipetteAbortType.PipetteStemHardbrake);
                    if (abortFlag.AbortOnTipCollision2)
                    {
                        double actualTriggeredPos = _pipette.GetTriggeredPositions(index, PipetteAbortType.PipetteStemHardbrake).OnTipCollision2;
                        if (System.Math.Abs(actualTriggeredPos - expectedTriggeredPos) < _tipValidationConfigs[index].ValidTipCaddyTolerance)
                        {
                            errCode = FloErrorCode.NoError;
                        }
                        else
                        {
                            errCode = FloErrorCode.PickTipWrongTipCaddyDetected;
                        }
                    }
                    else if (abortFlag.AbortOnStemCurrent)
                    {
                        _logger.LogError($"Pip{index},PickTipFirstMove,current sensor triggered,expected collision");
                        errCode = FloErrorCode.PickTipWrongSensorTriggered;
                    }
                    else
                    {
                        _logger.LogError($"Pip{index},PickTipFirstMove,no sensor triggered");
                        errCode = FloErrorCode.PickTipSensorNotTriggered;
                    }

                    _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                    _logger.LogDebug($"Pip{index},PickTipFirstMove,targetPos={targetPos},expectedTriggeredPos={expectedTriggeredPos},end,return");
                    return errCode;
                }

            if (errorCode == FloErrorCode.NoError)
            {
                errorCode = PickTipSecondMove(index, targetPos, tipCapacity, ref tipType, isGroup);
                private FloErrorCode PickTipSecondMove(uint index, double targetPos, TipCapacity tipCapacity, ref TipType tipType, bool isGroup)
                {
                    _logger.LogDebug($"Pip{index},PickTipSecondMove,targetPos={targetPos},tipCapacity={tipCapacity},tipType={tipType},isGroup={isGroup},start");
                    FloErrorCode errCode = FloErrorCode.NoError;

                    //abort stem movement when current exceeded
                    _pipette.SetAbortThreshold(index, AbortAnalogInput.StemCurrentSensor, _pickTipConfigs[index].SecondCurrentSensorThreshold);
                    _stemHardBrakeConfig[index].AbortInputFlag.AbortOnStemCurrent = true;
                    _pipette.SetAbortConfig(index, _stemHardBrakeConfig[index]);

                    errCode = _pipette.Move(index, _positionsBeforePickTip[index] - _pickTipConfigs[index].SecondMoveDownDistance, _pickTipConfigs[index].SecondMoveStemSpeed, _pickTipConfigs[index].SecondMoveStemAccel);
                    if (errCode != FloErrorCode.NoError)
                    {
                        _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                        _logger.LogDebug($"Pip{index},PickTipSecondMove,end,return={errCode}");
                        return errCode;
                    }

                    errCode = _pipette.WaitEOM(index);
                    if (errCode != FloErrorCode.NoError)
                    {
                        _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                        _logger.LogDebug($"Pip{index},PickTipSecondMove,end,return={errCode}");
                        return errCode;
                    }

                    //check if current abort input is really triggered
                    var triggeredInput = _pipette.GetTriggeredInputs(index, PipetteAbortType.PipetteStemHardbrake);
                    if (triggeredInput.AbortOnStemCurrent)
                    {
                        _logger.LogError($"Pip{index},PickTipSecondMove,current sensor triggered");
                        errCode = FloErrorCode.PickTipWrongSensorTriggered;

                        _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                        _pipette.GetPos(index, out double currentPos2);
                        double targetRetractPos2 = currentPos2 + _pickTipConfigs[index].PicktipSafeRetractStemDistance;
                        _pipette.Move(index, targetRetractPos2, _pickTipConfigs[index].PicktipRetractSpeed, _pickTipConfigs[index].PicktipRetractAccel);
                        _pipette.WaitPosition(index, targetRetractPos2 - _pickTipConfigs[index].WaitPositionOffset, true);
                        return errCode;
                    }

                    _pipette.ClearZHardBrakeAbortConfigAndFaults(index);

                    _pipette.GetPos(index, out double currentPos);
                    _targetRetractPos[index] = currentPos + _pickTipConfigs[index].PicktipSafeRetractStemDistance;

                    if (isGroup)
                    {
                        errCode = _pipette.Move(index, _positionsBeforePickTip[index], _pickTipConfigs[index].PicktipRetractSpeed, _pickTipConfigs[index].PicktipRetractAccel);
                        if (errCode != FloErrorCode.NoError)
                        {
                            _logger.LogDebug($"Pip{index},PickTipSecondMove,end,return={errCode}");
                            return errCode;
                        }

                        Thread.Sleep(_pickTipConfigs[index].DelayBeforeValidateTip);
                        errCode = _pipette.WaitEOM(index);
                    }
                    else
                    {
                        errCode = _pipette.Move(index, _targetRetractPos[index], _pickTipConfigs[index].PicktipRetractSpeed, _pickTipConfigs[index].PicktipRetractAccel);
                        if (errCode != FloErrorCode.NoError)
                        {
                            _logger.LogDebug($"Pip{index},PickTipSecondMove,end,return={errCode}");
                            return errCode;
                        }

                        //tip validation
                        Thread.Sleep(_pickTipConfigs[index].DelayBeforeValidateTip);
                        errCode = ValidateTipPickup(index, tipCapacity, ref tipType);
                            public FloErrorCode ValidateTipPickup(uint index, TipCapacity tipCapacity, ref TipType tipType)
                                {
                                    _logger.LogDebug($"Pip{index},ValidateTipPickup,tipCapacity={tipCapacity},tipType={tipType},start");

                                    if (_pipette.IsSimulated(index))
                                    {
                                        _logger.LogDebug($"Pip{index},ValidateTipPickup,end,simulated");
                                        return FloErrorCode.NoError;
                                    }

                                    FloErrorCode valid = FloErrorCode.NoError;
                                    TipKey tipKey = new TipKey(tipCapacity, tipType);

                                    double press2 = 0;
                                    double collision = 0;
                                    double resistance = 0;
                                    _resistanceValidationResults[index] = false;

                                    for (int count = 0; count < _tipValidationConfigs[index].ValidationSampleNum; count++)
                                    {
                                        press2 += _pipette.ReadAnalogSensor(index, AnalogSensor.Pressure, (short)SensorID.Pressure2);
                                        collision += _pipette.ReadAnalogSensor(index, AnalogSensor.Collision);
                                        resistance += _pipette.ReadAnalogSensor(index, AnalogSensor.Dllt);
                                        Thread.Sleep(_tipValidationConfigs[index].ValidationSamplingDelay);
                                    }

                                    ValidPressureLimit validPressureLimit = _tipKeyValidPressureLimits[tipKey][index];
                                    double avgPress2 = press2 / _tipValidationConfigs[index].ValidationSampleNum;
                                    double deltaPress2 = avgPress2 - _atmPressureValues[index];

                                    if (_pipette.IsSimulatedPressureReg())
                                    {
                                        _pressure2ValidationResults[index] = true;
                                    }
                                    else
                                    {
                                        _pressure2ValidationResults[index] = deltaPress2 <= validPressureLimit.ValidPressure2MaximumLimit && deltaPress2 >= validPressureLimit.ValidPressure2MinimumLimit;
                                    }

                                    TipType originalTipType = tipType;
                                    if (!_pressure2ValidationResults[index])
                                    {
                                        _logger.LogWarning($"Pip{index},ValidateTipPickup,invalid pressure 2 sensor,atmPressure={_atmPressureValues[index]},press2={avgPress2},thresholdMin={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MinimumLimit},thresholdMax={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MaximumLimit}");
                                        TipType[] tipTypes = (TipType[])Enum.GetValues(typeof(TipType));
                                        for (int i = 0; i < tipTypes.Length; i++)
                                        {
                                            if (tipType != tipTypes[i])
                                            {
                                                _logger.LogDebug($"Pip{index},ValidateTipPickup,try check with {tipTypes[i].ToString()} pressure threshold");

                                                TipKey newTipKey = new TipKey(tipCapacity, tipTypes[i]);
                                                ValidPressureLimit otherValidPressureLimit = _tipKeyValidPressureLimits[newTipKey][index];
                                                _pressure2ValidationResults[index] = deltaPress2 <= otherValidPressureLimit.ValidPressure2MaximumLimit && deltaPress2 >= otherValidPressureLimit.ValidPressure2MinimumLimit;

                                                if (_pressure2ValidationResults[index])
                                                {
                                                    _correctTipTypeResults[index] = false;
                                                    tipType = tipTypes[i];
                                                    break;
                                                }
                                                else
                                                {
                                                    _logger.LogWarning($"Pip{index},ValidateTipPickup,invalid pressure 2 sensor,atmPressure={_atmPressureValues[index]},press2={avgPress2},thresholdMin={otherValidPressureLimit.ValidPressure2MinimumLimit},thresholdMax={otherValidPressureLimit.ValidPressure2MaximumLimit}");
                                                }
                                            }
                                        }
                                    }
                                    else
                                    {
                                        _correctTipTypeResults[index] = true;
                                    }

                                    collision /= _tipValidationConfigs[index].ValidationSampleNum;
                                    _collisionValidationResults[index] = collision >= _tipValidationConfigs[index].ValidCollisionMinimumLimit && collision <= _tipValidationConfigs[index].ValidCollisionMaximumLimit;
                                    resistance /= _tipValidationConfigs[index].ValidationSampleNum;

                                    //calculate relative resistance delta (before and after pick tip)
                                    resistance = _initialResistanceValues[index] - resistance;
                                    _resistanceValidationResults[index] = resistance >= _tipValidationConfigs[index].ValidResistanceMinimumLimit && resistance <= _tipValidationConfigs[index].ValidResistanceMaximumLimit;

                                    //Be careful when re-order sensor checking sequence, please check 'valid' value is correct
                                    if (!_pressure2ValidationResults[index])
                                    {
                                        valid = FloErrorCode.PickTipPressureSensorValidationFailed;
                                    }

                                    if (originalTipType == TipType.Filter && !_correctTipTypeResults[index])
                                    {
                                        _logger.LogWarning($"Pip{index},ValidateTipPickup,wrong tip filter detected,atmPressure={_atmPressureValues[index]},press2={avgPress2},thresholdMin={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MinimumLimit},thresholdMax={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MaximumLimit}");
                                        valid = FloErrorCode.PickTipWrongTipFilterDetected;
                                    }
                                    else
                                    {
                                        _logger.LogDebug($"Pip{index},ValidateTipPickup,wrong tip caddy detected,atmPressure={_atmPressureValues[index]},press2={avgPress2},thresholdMin={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MinimumLimit},thresholdMax={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MaximumLimit}");
                                    }

                                    if (!_resistanceValidationResults[index])
                                    {
                                        _logger.LogWarning($"Pip{index},ValidateTipPickup,invalid resistance sensor,value={resistance},thresholdMin={_tipValidationConfigs[index].ValidResistanceMinimumLimit},thresholdMax={_tipValidationConfigs[index].ValidResistanceMaximumLimit}");
                                        if (valid == FloErrorCode.NoError)
                                        {
                                            valid = FloErrorCode.PickTipResistanceSensorValidationFailed;
                                        }
                                        else
                                        {
                                            valid = FloErrorCode.PickTipPressureAndResistanceSensorValidationFailed;
                                        }
                                    }
                                    else
                                    {
                                        _logger.LogDebug($"Pip{index},ValidateTipPickup,resistance sensor,value={resistance},thresholdMin={_tipValidationConfigs[index].ValidResistanceMinimumLimit},thresholdMax={_tipValidationConfigs[index].ValidResistanceMaximumLimit}");
                                    }

                                    if (!_collisionValidationResults[index])
                                    {
                                        _logger.LogWarning($"Pip{index},ValidateTipPickup,invalid collision sensor,value={collision},thresholdMin={_tipValidationConfigs[index].ValidCollisionMinimumLimit},thresholdMax={_tipValidationConfigs[index].ValidCollisionMaximumLimit}");
                                        if (valid == FloErrorCode.NoError)
                                        {
                                            valid = FloErrorCode.PickTipCollisionSensorValidationFailed;
                                        }
                                        else if (valid == FloErrorCode.PickTipPressureSensorValidationFailed)
                                        {
                                            valid = FloErrorCode.PickTipPressureAndCollisionSensorValidationFailed;
                                        }
                                        else if (valid == FloErrorCode.PickTipResistanceSensorValidationFailed)
                                        {
                                            valid = FloErrorCode.PickTipResistanceAndCollisionSensorValidationFailed;
                                        }
                                        else
                                        {
                                            valid = FloErrorCode.PickTipAllSensorsValidationFailed;
                                        }
                                    }
                                    else
                                    {
                                        _logger.LogDebug($"Pip{index},ValidateTipPickup,collision sensor,value={collision},thresholdMin={_tipValidationConfigs[index].ValidCollisionMinimumLimit},thresholdMax={_tipValidationConfigs[index].ValidCollisionMaximumLimit}");
                                    }

                                    _logger.LogDebug($"Pip{index},ValidateTipPickup,tipCapacity={tipCapacity},tipType={tipType},end,return={valid}");
                                    return valid;
                                }

                        //wait position instead of waiting until stem stop moving to make movement smooth and fast.
                        //note: if validateTipPickup takes longer time, wait position is not useful.
                        _pipette.WaitPosition(index, _targetRetractPos[index] - _pickTipConfigs[index].WaitPositionOffset, true);
                    }

                    _logger.LogDebug($"Pip{index},PickTipSecondMove,targetPos={targetPos},tipCapacity={tipCapacity},tipType={tipType},isGroup={isGroup},end");
                    return errCode;
                }

            }

            _pipette.AbortFlowFunc(index); //on firmware
            _pipette.SetFolErrorConfig(index, folErrorEnabled, folErrorLimit); //on firmware
            _logger.LogDebug($"Pip{index},Execute,SetFolErrorConfig,isEnable={folErrorEnabled} value={folErrorLimit}");
            _pipette.SetTargetReachedParams(index, trackingWindow, trackingTimeMs); //on firmware
            _logger.LogDebug($"Pip{index},Execute,SetTargetReachedParams,trackingWindow={trackingWindow},trackingTimeMs={trackingTimeMs}");

            _logger.LogDebug($"Pip{index},Execute,targetPos={targetPos},tipCapacity={tipCapacity},tipType={tipType},expectedTriggeredPos={expectedTriggeredPos},retry={retry},isGroup={isGroup},end,return={errorCode}");
            return errorCode;
        }

        private FloErrorCode PickTipFirstMove(uint index, double targetPos, double expectedTriggeredPos)
        {
            _logger.LogDebug($"Pip{index},PickTipFirstMove,targetPos={targetPos},expectedTriggeredPos={expectedTriggeredPos},start");
            FloErrorCode errCode;

            //make stem hard brake if collision sensor or current sensor reading exceed limit
            double collisionTreshold = _pipette.ReadAnalogSensor(index, AnalogSensor.Collision) - _pickTipConfigs[index].AbortCollisionThreshold;
            _pipette.SetAbortThreshold(index, AbortAnalogInput.CollisionSensor2, collisionTreshold);
            _pipette.SetAbortThreshold(index, AbortAnalogInput.StemCurrentSensor, _pickTipConfigs[index].FirstCurrentSensorThreshold);
            _stemHardBrakeConfig[index].AbortInputFlag.AbortOnTipCollision2 = true;
            _stemHardBrakeConfig[index].AbortInputFlag.AbortOnStemCurrent = true;
            _pipette.SetAbortConfig(index, _stemHardBrakeConfig[index]);

            errCode = _pipette.Move(index, targetPos, _pickTipConfigs[index].FirstMoveStemSpeed, _pickTipConfigs[index].FirstMoveStemAccel);
            if (errCode != FloErrorCode.NoError)
            {
                _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                _logger.LogDebug($"Pip{index},PickTipFirstMove,end,return={errCode}");
                return errCode;
            }

            errCode = _pipette.WaitEOM(index);
            if (errCode != FloErrorCode.NoError)
            {
                _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                _logger.LogDebug($"Pip{index},PickTipFirstMove,end,return={errCode}");
                return errCode;
            }

            var abortFlag = _pipette.GetTriggeredInputs(index, PipetteAbortType.PipetteStemHardbrake);
            if (abortFlag.AbortOnTipCollision2)
            {
                double actualTriggeredPos = _pipette.GetTriggeredPositions(index, PipetteAbortType.PipetteStemHardbrake).OnTipCollision2;
                if (System.Math.Abs(actualTriggeredPos - expectedTriggeredPos) < _tipValidationConfigs[index].ValidTipCaddyTolerance)
                {
                    errCode = FloErrorCode.NoError;
                }
                else
                {
                    errCode = FloErrorCode.PickTipWrongTipCaddyDetected;
                }
            }
            else if (abortFlag.AbortOnStemCurrent)
            {
                _logger.LogError($"Pip{index},PickTipFirstMove,current sensor triggered,expected collision");
                errCode = FloErrorCode.PickTipWrongSensorTriggered;
            }
            else
            {
                _logger.LogError($"Pip{index},PickTipFirstMove,no sensor triggered");
                errCode = FloErrorCode.PickTipSensorNotTriggered;
            }

            _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
            _logger.LogDebug($"Pip{index},PickTipFirstMove,targetPos={targetPos},expectedTriggeredPos={expectedTriggeredPos},end,return");
            return errCode;
        }

        private FloErrorCode PickTipSecondMove(uint index, double targetPos, TipCapacity tipCapacity, ref TipType tipType, bool isGroup)
        {
            _logger.LogDebug($"Pip{index},PickTipSecondMove,targetPos={targetPos},tipCapacity={tipCapacity},tipType={tipType},isGroup={isGroup},start");
            FloErrorCode errCode = FloErrorCode.NoError;

            //abort stem movement when current exceeded
            _pipette.SetAbortThreshold(index, AbortAnalogInput.StemCurrentSensor, _pickTipConfigs[index].SecondCurrentSensorThreshold);
            _stemHardBrakeConfig[index].AbortInputFlag.AbortOnStemCurrent = true;
            _pipette.SetAbortConfig(index, _stemHardBrakeConfig[index]);

            errCode = _pipette.Move(index, _positionsBeforePickTip[index] - _pickTipConfigs[index].SecondMoveDownDistance, _pickTipConfigs[index].SecondMoveStemSpeed, _pickTipConfigs[index].SecondMoveStemAccel);
            if (errCode != FloErrorCode.NoError)
            {
                _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                _logger.LogDebug($"Pip{index},PickTipSecondMove,end,return={errCode}");
                return errCode;
            }

            errCode = _pipette.WaitEOM(index);
            if (errCode != FloErrorCode.NoError)
            {
                _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                _logger.LogDebug($"Pip{index},PickTipSecondMove,end,return={errCode}");
                return errCode;
            }

            //check if current abort input is really triggered
            var triggeredInput = _pipette.GetTriggeredInputs(index, PipetteAbortType.PipetteStemHardbrake);
            if (triggeredInput.AbortOnStemCurrent)
            {
                _logger.LogError($"Pip{index},PickTipSecondMove,current sensor triggered");
                errCode = FloErrorCode.PickTipWrongSensorTriggered;

                _pipette.ClearZHardBrakeAbortConfigAndFaults(index);
                _pipette.GetPos(index, out double currentPos2);
                double targetRetractPos2 = currentPos2 + _pickTipConfigs[index].PicktipSafeRetractStemDistance;
                _pipette.Move(index, targetRetractPos2, _pickTipConfigs[index].PicktipRetractSpeed, _pickTipConfigs[index].PicktipRetractAccel);
                _pipette.WaitPosition(index, targetRetractPos2 - _pickTipConfigs[index].WaitPositionOffset, true);
                return errCode;
            }

            _pipette.ClearZHardBrakeAbortConfigAndFaults(index);

            _pipette.GetPos(index, out double currentPos);
            _targetRetractPos[index] = currentPos + _pickTipConfigs[index].PicktipSafeRetractStemDistance;

            if (isGroup)
            {
                errCode = _pipette.Move(index, _positionsBeforePickTip[index], _pickTipConfigs[index].PicktipRetractSpeed, _pickTipConfigs[index].PicktipRetractAccel);
                if (errCode != FloErrorCode.NoError)
                {
                    _logger.LogDebug($"Pip{index},PickTipSecondMove,end,return={errCode}");
                    return errCode;
                }

                Thread.Sleep(_pickTipConfigs[index].DelayBeforeValidateTip);
                errCode = _pipette.WaitEOM(index);
            }
            else
            {
                errCode = _pipette.Move(index, _targetRetractPos[index], _pickTipConfigs[index].PicktipRetractSpeed, _pickTipConfigs[index].PicktipRetractAccel);
                if (errCode != FloErrorCode.NoError)
                {
                    _logger.LogDebug($"Pip{index},PickTipSecondMove,end,return={errCode}");
                    return errCode;
                }

                //tip validation
                Thread.Sleep(_pickTipConfigs[index].DelayBeforeValidateTip);
                errCode = ValidateTipPickup(index, tipCapacity, ref tipType);

                //wait position instead of waiting until stem stop moving to make movement smooth and fast.
                //note: if validateTipPickup takes longer time, wait position is not useful.
                _pipette.WaitPosition(index, _targetRetractPos[index] - _pickTipConfigs[index].WaitPositionOffset, true);
            }

            _logger.LogDebug($"Pip{index},PickTipSecondMove,targetPos={targetPos},tipCapacity={tipCapacity},tipType={tipType},isGroup={isGroup},end");
            return errCode;
        }

        public void ReadInitialSensor(uint index)
        {
            _logger.LogDebug($"Pip{index},ReadInitialSensor,start");

            _initialResistanceValues[index] = 0;
            _atmPressureValues[index] = _pipette.GetAtmPressure(index);

            for (int i = 0; i < _tipValidationConfigs[index].ValidationSampleNum; i++)
            {
                _initialResistanceValues[index] += _pipette.ReadAnalogSensor(index, AnalogSensor.Dllt);
                Thread.Sleep(_tipValidationConfigs[index].ValidationSamplingDelay);
            }
            _initialResistanceValues[index] /= _tipValidationConfigs[index].ValidationSampleNum;

            _logger.LogDebug($"Pip{index},ReadInitialSensor,end,resistance={_initialResistanceValues[index]},atmPressure={_atmPressureValues[index]}");
        }

        public FloErrorCode ValidateTipPickup(uint index, TipCapacity tipCapacity, ref TipType tipType)
        {
            _logger.LogDebug($"Pip{index},ValidateTipPickup,tipCapacity={tipCapacity},tipType={tipType},start");

            if (_pipette.IsSimulated(index))
            {
                _logger.LogDebug($"Pip{index},ValidateTipPickup,end,simulated");
                return FloErrorCode.NoError;
            }

            FloErrorCode valid = FloErrorCode.NoError;
            TipKey tipKey = new TipKey(tipCapacity, tipType);

            double press2 = 0;
            double collision = 0;
            double resistance = 0;
            _resistanceValidationResults[index] = false;

            for (int count = 0; count < _tipValidationConfigs[index].ValidationSampleNum; count++)
            {
                press2 += _pipette.ReadAnalogSensor(index, AnalogSensor.Pressure, (short)SensorID.Pressure2);
                collision += _pipette.ReadAnalogSensor(index, AnalogSensor.Collision);
                resistance += _pipette.ReadAnalogSensor(index, AnalogSensor.Dllt);
                Thread.Sleep(_tipValidationConfigs[index].ValidationSamplingDelay);
            }

            ValidPressureLimit validPressureLimit = _tipKeyValidPressureLimits[tipKey][index];
            double avgPress2 = press2 / _tipValidationConfigs[index].ValidationSampleNum;
            double deltaPress2 = avgPress2 - _atmPressureValues[index];

            if (_pipette.IsSimulatedPressureReg())
            {
                _pressure2ValidationResults[index] = true;
            }
            else
            {
                _pressure2ValidationResults[index] = deltaPress2 <= validPressureLimit.ValidPressure2MaximumLimit && deltaPress2 >= validPressureLimit.ValidPressure2MinimumLimit;
            }

            TipType originalTipType = tipType;
            if (!_pressure2ValidationResults[index])
            {
                _logger.LogWarning($"Pip{index},ValidateTipPickup,invalid pressure 2 sensor,atmPressure={_atmPressureValues[index]},press2={avgPress2},thresholdMin={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MinimumLimit},thresholdMax={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MaximumLimit}");
                TipType[] tipTypes = (TipType[])Enum.GetValues(typeof(TipType));
                for (int i = 0; i < tipTypes.Length; i++)
                {
                    if (tipType != tipTypes[i])
                    {
                        _logger.LogDebug($"Pip{index},ValidateTipPickup,try check with {tipTypes[i].ToString()} pressure threshold");

                        TipKey newTipKey = new TipKey(tipCapacity, tipTypes[i]);
                        ValidPressureLimit otherValidPressureLimit = _tipKeyValidPressureLimits[newTipKey][index];
                        _pressure2ValidationResults[index] = deltaPress2 <= otherValidPressureLimit.ValidPressure2MaximumLimit && deltaPress2 >= otherValidPressureLimit.ValidPressure2MinimumLimit;

                        if (_pressure2ValidationResults[index])
                        {
                            _correctTipTypeResults[index] = false;
                            tipType = tipTypes[i];
                            break;
                        }
                        else
                        {
                            _logger.LogWarning($"Pip{index},ValidateTipPickup,invalid pressure 2 sensor,atmPressure={_atmPressureValues[index]},press2={avgPress2},thresholdMin={otherValidPressureLimit.ValidPressure2MinimumLimit},thresholdMax={otherValidPressureLimit.ValidPressure2MaximumLimit}");
                        }
                    }
                }
            }
            else
            {
                _correctTipTypeResults[index] = true;
            }

            collision /= _tipValidationConfigs[index].ValidationSampleNum;
            _collisionValidationResults[index] = collision >= _tipValidationConfigs[index].ValidCollisionMinimumLimit && collision <= _tipValidationConfigs[index].ValidCollisionMaximumLimit;
            resistance /= _tipValidationConfigs[index].ValidationSampleNum;

            //calculate relative resistance delta (before and after pick tip)
            resistance = _initialResistanceValues[index] - resistance;
            _resistanceValidationResults[index] = resistance >= _tipValidationConfigs[index].ValidResistanceMinimumLimit && resistance <= _tipValidationConfigs[index].ValidResistanceMaximumLimit;

            //Be careful when re-order sensor checking sequence, please check 'valid' value is correct
            if (!_pressure2ValidationResults[index])
            {
                valid = FloErrorCode.PickTipPressureSensorValidationFailed;
            }

            if (originalTipType == TipType.Filter && !_correctTipTypeResults[index])
            {
                _logger.LogWarning($"Pip{index},ValidateTipPickup,wrong tip filter detected,atmPressure={_atmPressureValues[index]},press2={avgPress2},thresholdMin={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MinimumLimit},thresholdMax={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MaximumLimit}");
                valid = FloErrorCode.PickTipWrongTipFilterDetected;
            }
            else
            {
                _logger.LogDebug($"Pip{index},ValidateTipPickup,wrong tip caddy detected,atmPressure={_atmPressureValues[index]},press2={avgPress2},thresholdMin={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MinimumLimit},thresholdMax={_tipKeyValidPressureLimits[tipKey][index].ValidPressure2MaximumLimit}");
            }

            if (!_resistanceValidationResults[index])
            {
                _logger.LogWarning($"Pip{index},ValidateTipPickup,invalid resistance sensor,value={resistance},thresholdMin={_tipValidationConfigs[index].ValidResistanceMinimumLimit},thresholdMax={_tipValidationConfigs[index].ValidResistanceMaximumLimit}");
                if (valid == FloErrorCode.NoError)
                {
                    valid = FloErrorCode.PickTipResistanceSensorValidationFailed;
                }
                else
                {
                    valid = FloErrorCode.PickTipPressureAndResistanceSensorValidationFailed;
                }
            }
            else
            {
                _logger.LogDebug($"Pip{index},ValidateTipPickup,resistance sensor,value={resistance},thresholdMin={_tipValidationConfigs[index].ValidResistanceMinimumLimit},thresholdMax={_tipValidationConfigs[index].ValidResistanceMaximumLimit}");
            }

            if (!_collisionValidationResults[index])
            {
                _logger.LogWarning($"Pip{index},ValidateTipPickup,invalid collision sensor,value={collision},thresholdMin={_tipValidationConfigs[index].ValidCollisionMinimumLimit},thresholdMax={_tipValidationConfigs[index].ValidCollisionMaximumLimit}");
                if (valid == FloErrorCode.NoError)
                {
                    valid = FloErrorCode.PickTipCollisionSensorValidationFailed;
                }
                else if (valid == FloErrorCode.PickTipPressureSensorValidationFailed)
                {
                    valid = FloErrorCode.PickTipPressureAndCollisionSensorValidationFailed;
                }
                else if (valid == FloErrorCode.PickTipResistanceSensorValidationFailed)
                {
                    valid = FloErrorCode.PickTipResistanceAndCollisionSensorValidationFailed;
                }
                else
                {
                    valid = FloErrorCode.PickTipAllSensorsValidationFailed;
                }
            }
            else
            {
                _logger.LogDebug($"Pip{index},ValidateTipPickup,collision sensor,value={collision},thresholdMin={_tipValidationConfigs[index].ValidCollisionMinimumLimit},thresholdMax={_tipValidationConfigs[index].ValidCollisionMaximumLimit}");
            }

            _logger.LogDebug($"Pip{index},ValidateTipPickup,tipCapacity={tipCapacity},tipType={tipType},end,return={valid}");
            return valid;
        }

        public FloErrorCode RetractAfterPickTip(uint index)
        {
            _logger.LogDebug($"Pip{index},RetractAfterPickTip,start");
            FloErrorCode errorCode = _pipette.Move(index, _targetRetractPos[index], _pickTipConfigs[index].PicktipRetractSpeed, _pickTipConfigs[index].PicktipRetractAccel);
            if (errorCode == FloErrorCode.NoError)
            {
                errorCode = _pipette.WaitPosition(index, _targetRetractPos[index] - _pickTipConfigs[index].WaitPositionOffset, true);
            }
            _logger.LogDebug($"Pip{index},RetractAfterPickTip,end,return={errorCode}");
            return errorCode;
        }
    }
}
