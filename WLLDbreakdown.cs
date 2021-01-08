public FloErrorCode FindSurface( uint index, double lowestTargetPosition, out double surfacePos )
		{
			if( _pipette.IsSimulated( index ) )
			{
				_logger.LogDebug( $"Pip{index},FindSurface,simulated" );
				surfacePos = 0;
				return FloErrorCode.NoError;
			}

			_firmwareLogger.Start( index, _firmwareLogConfigs[index].StemMotorMask, _firmwareLogConfigs[index].SensorMask, FirmwareLoggerService.BuildHeaderMessage( _firmwareLogConfigs[index].HeaderMessage, _firmwareLogConfigs[index].HeaderMessageDateFormat ) );

			lowestTargetPosition -= _collisionCompressionTolerances[index]; //add with spring z tolerance

			_logger.LogDebug( $"Pip{index},FindSurface,start,lowestPos{lowestTargetPosition}" );

			_pipette.SetAd9833Frequency( index, _wlldConfigs[index].Ad9833Frequency );
			Thread.Sleep( _wlldConfigs[index].SetFrequencyDelay );
			_pipette.ClearZHardBrakeAbortConfigAndFaults( index );
			ClearValveInAbort( index );

			SetAbortWlld( index );
            // methods
                private void SetAbortWlld( uint index )
                    {
                        _pipette.SetAbortThreshold( index, AbortAnalogInput.CollisionSensor2, _pipette.ReadAnalogSensor( index, AnalogSensor.Collision ) - _wlldConfigs[index].AbortCollisionThreshold );
                        _pipette.SetAbortThreshold( index, AbortAnalogInput.LiquidLevelSensor, _pipette.ReadAnalogSensor( index, AnalogSensor.Dllt ) - _wlldConfigs[index].AbortResistanceThreshold );
                        _pipette.SetAbortThreshold( index, AbortAnalogInput.StemCurrentSensor, _wlldConfigs[index].CurrentSensorThreshold );

                        _stemHardBrakeConfigs[index].AbortDelay = 0;
                        _stemHardBrakeConfigs[index].TriggerOnAll = false;
                        _stemHardBrakeConfigs[index].AbortInputFlag.AbortOnTipCollision2 = true;
                        _stemHardBrakeConfigs[index].AbortInputFlag.AbortOnLiquidLevelSensor = true;
                        _stemHardBrakeConfigs[index].AbortInputFlag.AbortOnStemCurrent = true;
                        _pipette.SetAbortConfig( index, _stemHardBrakeConfigs[index] );

                        _valveInConfigs[index].AbortDelay = 0;
                        _valveInConfigs[index].TriggerOnAll = false;
                        _valveInConfigs[index].AbortInputFlag.AbortOnTipCollision2 = true;
                        _valveInConfigs[index].AbortInputFlag.AbortOnLiquidLevelSensor = true;
                        _valveInConfigs[index].AbortInputFlag.AbortOnStemCurrent = true;
                        _pipette.SetAbortConfig( index, _valveInConfigs[index] );
                    }

			FloErrorCode errCode = _pipette.Move( index, lowestTargetPosition, _wlldConfigs[index].StemVel, _wlldConfigs[index].StemAccel );
			if( errCode == FloErrorCode.NoError )
			{
				_pipette.WaitEOM( index );
			}

			var abortFlags = _pipette.GetTriggeredInputs( index, PipetteAbortType.PipetteStemHardbrake );

			if( abortFlags.AbortOnTipCollision2 )
			{
				//dry dispense possible
				_logger.LogWarning( $"Pip{index},FindSurface,Pressure={_pipette.GetTriggeredValue( index, PipetteAbortType.PipetteStemNormal, PipetteAbortInputBitMasks.Collision2 )},collision detected" );
				errCode = FloErrorCode.CollisionTriggered;
			}
			else if( abortFlags.AbortOnLiquidLevelSensor )
			{
				//liquid surface found
				_logger.LogDebug( $"Pip{index},FindSurface,liquid surface found,Resistance={_pipette.GetTriggeredValue( index, PipetteAbortType.PipetteStemHardbrake, PipetteAbortInputBitMasks.LiquidLevelSensor )}" );
				errCode = FloErrorCode.NoError;
			}
			else if( abortFlags.AbortOnStemCurrent )
			{
				_logger.LogWarning( $"Pip{index},FindSurface,stem over current" );
				errCode = FloErrorCode.OverCurrent;
			}
			else
			{
				_logger.LogWarning( $"Pip{index},FindSurface,travel limit reached" );
				errCode = FloErrorCode.TravelLimitReached;
			}
			_firmwareLogger.StopAndSaveToFile( index, FirmwareLoggerService.BuildHeaderMessage( _firmwareLogConfigs[index].FileName, _firmwareLogConfigs[index].FileNameDateFormat ) );
			_pipette.ClearZHardBrakeAbortConfigAndFaults( index );
			ClearValveInAbort( index );
            //methods
                private void ClearValveInAbort( uint index )
                    {
                    _valveInConfigs[index].AbortInputFlag.AbortOnTipCollision2 = false;
                    _valveInConfigs[index].AbortInputFlag.AbortOnLiquidLevelSensor = false;
                    _valveInConfigs[index].AbortInputFlag.AbortOnStemCurrent = false;
                    _pipette.SetAbortConfig( index, _valveInConfigs[index] );
                    _pipette.ClearTriggeredInputs( index, PipetteAbortType.ValveIn );
                    }

			_pipette.GetPos( index, out surfacePos );
			_logger.LogDebug( $"Pip{index},FindSurface,end,surfacePos={surfacePos},errorCode={errCode}" );
			return errCode;
			}

		
		
		
		