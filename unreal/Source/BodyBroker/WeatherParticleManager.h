// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "AudioManager.h"
#include "WeatherManager.h"
#include "WeatherParticleManager.generated.h"

/**
 * WeatherParticleManager - Manages Niagara particle systems for weather effects
 * WS-002: Niagara Particle Systems
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class BODYBROKER_API UWeatherParticleManager : public UActorComponent
{
	GENERATED_BODY()

public:
	UWeatherParticleManager(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/**
	 * Set weather state and update particle systems.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Particles|WS-002")
	void SetWeatherState(EWeatherState WeatherState, float Intensity);

	/**
	 * Enable/disable rain particle system.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Particles|WS-002")
	void SetRainEnabled(bool bEnabled, float Intensity);

	/**
	 * Enable/disable snow particle system.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Particles|WS-002")
	void SetSnowEnabled(bool bEnabled, float Intensity);

	/**
	 * Enable/disable fog volumetric system.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Particles|WS-002")
	void SetFogEnabled(bool bEnabled, float Density);

	/**
	 * Trigger lightning strike visual effect.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Particles|WS-002")
	void TriggerLightningStrike(FVector StrikeLocation, float Intensity);

	/**
	 * Set particle LOD level.
	 */
	UFUNCTION(BlueprintCallable, Category = "Weather Particles|WS-002")
	void SetParticleLOD(int32 LODLevel);

private:
	// Niagara components for weather effects
	UPROPERTY()
	TObjectPtr<UNiagaraComponent> RainParticleComponent;

	UPROPERTY()
	TObjectPtr<UNiagaraComponent> SnowParticleComponent;

	UPROPERTY()
	TObjectPtr<UNiagaraComponent> FogVolumetricComponent;

	UPROPERTY()
	TObjectPtr<UNiagaraComponent> LightningComponent;

	// Niagara system assets
	UPROPERTY()
	TObjectPtr<UNiagaraSystem> RainSystem;

	UPROPERTY()
	TObjectPtr<UNiagaraSystem> SnowSystem;

	UPROPERTY()
	TObjectPtr<UNiagaraSystem> FogSystem;

	UPROPERTY()
	TObjectPtr<UNiagaraSystem> LightningSystem;

	// Current weather state
	UPROPERTY()
	EWeatherState CurrentWeatherState;

	// Current intensity
	UPROPERTY()
	float CurrentIntensity;

	// Particle LOD level
	UPROPERTY()
	int32 ParticleLODLevel;

	// Load Niagara systems
	void LoadNiagaraSystems();

	// Create or get Niagara component
	UNiagaraComponent* GetOrCreateNiagaraComponent(TObjectPtr<UNiagaraSystem> System, TObjectPtr<UNiagaraComponent>& ComponentRef);

	// Update particle parameters based on intensity
	void UpdateParticleParameters(UNiagaraComponent* Component, float Intensity);

	// Pool Niagara components for reuse
	TArray<TObjectPtr<UNiagaraComponent>> NiagaraComponentPool;

	// Get pooled component or create new
	UNiagaraComponent* AcquirePooledComponent(TObjectPtr<UNiagaraSystem> System);
	void ReleasePooledComponent(UNiagaraComponent* Component);
};

