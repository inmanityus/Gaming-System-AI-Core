// Copyright Epic Games, Inc. All Rights Reserved.

#include "LipSyncComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/AudioComponent.h"
#include "DialogueManager.h"
#include "Engine/World.h"
#include "Sound/SoundWave.h"

ULipSyncComponent::ULipSyncComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
	, CurrentPhonemeIndex(0)
	, CurrentPlaybackTime(0.0f)
	, bLipSyncEnabled(true)
{
	PrimaryComponentTick.bCanEverTick = true;
	bTickInEditor = false;
}

void ULipSyncComponent::BeginPlay()
{
	Super::BeginPlay();
	FindSkeletalMeshComponent();
	UE_LOG(LogTemp, Log, TEXT("LipSyncComponent: BeginPlay"));
}

void ULipSyncComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (bLipSyncEnabled && CurrentLipSyncData.Frames.Num() > 0)
	{
		UpdateJawAnimation(DeltaTime);
	}
}

void ULipSyncComponent::StartLipSync(const FLipSyncData& LipSyncData)
{
	CurrentLipSyncData = LipSyncData;
	CurrentPhonemeIndex = 0;
	CurrentPlaybackTime = 0.0f;

	UE_LOG(LogTemp, Log, TEXT("LipSyncComponent: Started lip-sync with %d phoneme frames"), LipSyncData.Frames.Num());
}

void ULipSyncComponent::StopLipSync()
{
	CurrentLipSyncData = FLipSyncData();
	CurrentPhonemeIndex = 0;
	CurrentPlaybackTime = 0.0f;

	// Reset all visemes
	if (SkeletalMeshComponent)
	{
		// Reset jaw and mouth blend shapes
		SkeletalMeshComponent->SetMorphTarget(FName(TEXT("JawOpen")), 0.0f, false);
		SkeletalMeshComponent->SetMorphTarget(FName(TEXT("MouthOpen")), 0.0f, false);
	}

	UE_LOG(LogTemp, Log, TEXT("LipSyncComponent: Stopped lip-sync"));
}

void ULipSyncComponent::ExtractPhonemesFromAudio(UAudioComponent* AudioComponent, FLipSyncData& OutLipSyncData)
{
	if (!AudioComponent)
	{
		return;
	}

	USoundWave* SoundWave = Cast<USoundWave>(AudioComponent->GetSound());
	if (!SoundWave)
	{
		UE_LOG(LogTemp, Warning, TEXT("LipSyncComponent: ExtractPhonemesFromAudio - SoundWave not available"));
		return;
	}

	const float Duration = SoundWave->GetDuration();
	if (Duration <= KINDA_SMALL_NUMBER)
	{
		return;
	}

	constexpr float FrameLengthSeconds = 0.12f; // ~120ms per phoneme frame
	const int32 FrameCount = FMath::Max(1, FMath::CeilToInt(Duration / FrameLengthSeconds));

	const uint8* RawPCMData = SoundWave->RawPCMData;
	const int32 RawPCMSize = SoundWave->RawPCMDataSize;
	const int32 NumChannels = SoundWave->NumChannels > 0 ? SoundWave->NumChannels : 1;
	const float SampleRate = SoundWave->GetSampleRateForCurrentPlatform() > 0
		? static_cast<float>(SoundWave->GetSampleRateForCurrentPlatform())
		: 44100.0f;

	OutLipSyncData.Frames.Empty(FrameCount);

	if (RawPCMData && RawPCMSize > 0)
	{
		const int16* SampleData = reinterpret_cast<const int16*>(RawPCMData);
		const int32 TotalSamples = RawPCMSize / sizeof(int16);
		const int32 SamplesPerFrame = FMath::Max(1, FMath::FloorToInt(SampleRate * FrameLengthSeconds) * NumChannels);

		for (int32 FrameIndex = 0; FrameIndex < FrameCount; ++FrameIndex)
		{
			const int32 StartSample = FMath::Min(FrameIndex * SamplesPerFrame, TotalSamples);
			const int32 EndSample = FMath::Min(StartSample + SamplesPerFrame, TotalSamples);

			int64 AccumulatedAmplitude = 0;
			for (int32 SampleIdx = StartSample; SampleIdx < EndSample; ++SampleIdx)
			{
				AccumulatedAmplitude += FMath::Abs(SampleData[SampleIdx]);
			}

			const int32 SampleCount = FMath::Max(1, EndSample - StartSample);
			const float NormalizedEnergy = FMath::Clamp(static_cast<float>(AccumulatedAmplitude) / (SampleCount * 32768.0f), 0.0f, 1.0f);

			FPhonemeFrame Frame;
			Frame.StartTime = FrameIndex * FrameLengthSeconds;
			Frame.Duration = FrameLengthSeconds;
			Frame.Time = Frame.StartTime;
			Frame.Phoneme = SelectPhonemeForEnergy(NormalizedEnergy);
			Frame.Viseme = PhonemeToViseme(Frame.Phoneme);

			OutLipSyncData.Frames.Add(Frame);
		}
	}
	else
	{
		// Fallback: generate frames purely from duration if PCM data is unavailable
		for (int32 FrameIndex = 0; FrameIndex < FrameCount; ++FrameIndex)
		{
			FPhonemeFrame Frame;
			Frame.StartTime = FrameIndex * FrameLengthSeconds;
			Frame.Duration = FrameLengthSeconds;
			Frame.Time = Frame.StartTime;

			const float Phase = static_cast<float>(FrameIndex) / static_cast<float>(FrameCount);
			Frame.Phoneme = SelectPhonemeForEnergy(Phase);
			Frame.Viseme = PhonemeToViseme(Frame.Phoneme);

			OutLipSyncData.Frames.Add(Frame);
		}
	}

	UE_LOG(LogTemp, VeryVerbose, TEXT("LipSyncComponent: Generated %d phoneme frames via local analysis"), OutLipSyncData.Frames.Num());
}

void ULipSyncComponent::UpdateJawAnimation(float DeltaTime)
{
	if (!SkeletalMeshComponent || CurrentLipSyncData.Frames.Num() == 0)
	{
		return;
	}

	CurrentPlaybackTime += DeltaTime;

	// Find current phoneme frame
	while (CurrentPhonemeIndex < CurrentLipSyncData.Frames.Num() - 1)
	{
		if (CurrentPlaybackTime >= CurrentLipSyncData.Frames[CurrentPhonemeIndex + 1].Time)
		{
			CurrentPhonemeIndex++;
		}
		else
		{
			break;
		}
	}

	// Apply current viseme
	if (CurrentPhonemeIndex < CurrentLipSyncData.Frames.Num())
	{
		const FPhonemeFrame& CurrentFrame = CurrentLipSyncData.Frames[CurrentPhonemeIndex];
		FString VisemeName = CurrentFrame.Viseme.IsEmpty() ? PhonemeToViseme(CurrentFrame.Phoneme) : CurrentFrame.Viseme;
		
		// Apply viseme with weight based on time interpolation
		float Weight = 1.0f;
		if (CurrentPhonemeIndex < CurrentLipSyncData.Frames.Num() - 1)
		{
			float NextTime = CurrentLipSyncData.Frames[CurrentPhonemeIndex + 1].Time;
			float CurrentTime = CurrentFrame.Time;
			if (NextTime > CurrentTime)
			{
				Weight = 1.0f - ((CurrentPlaybackTime - CurrentTime) / (NextTime - CurrentTime));
			}
		}

		ApplyViseme(VisemeName, Weight);
	}
}

void ULipSyncComponent::SetLipSyncEnabled(bool bEnabled)
{
	bLipSyncEnabled = bEnabled;
	if (!bEnabled)
	{
		StopLipSync();
	}
}

void ULipSyncComponent::FindSkeletalMeshComponent()
{
	if (AActor* Owner = GetOwner())
	{
		SkeletalMeshComponent = Owner->FindComponentByClass<USkeletalMeshComponent>();
		if (SkeletalMeshComponent)
		{
			UE_LOG(LogTemp, Log, TEXT("LipSyncComponent: Found skeletal mesh component"));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("LipSyncComponent: No skeletal mesh component found"));
		}
	}
}

void ULipSyncComponent::ApplyViseme(const FString& VisemeName, float Weight)
{
	if (!SkeletalMeshComponent)
	{
		return;
	}

	// Map viseme names to blend shape weights
	// In production, use data table for viseme-to-blendshape mapping
	TMap<FString, float> VisemeWeights;

	if (VisemeName == TEXT("silence") || VisemeName.IsEmpty())
	{
		// Closed mouth
		VisemeWeights.Add(TEXT("JawOpen"), 0.0f);
		VisemeWeights.Add(TEXT("MouthOpen"), 0.0f);
	}
	else if (VisemeName == TEXT("p") || VisemeName == TEXT("b") || VisemeName == TEXT("m"))
	{
		// Closed lips
		VisemeWeights.Add(TEXT("JawOpen"), 0.0f);
		VisemeWeights.Add(TEXT("MouthOpen"), 0.0f);
		VisemeWeights.Add(TEXT("LipPucker"), 0.5f);
	}
	else if (VisemeName == TEXT("f") || VisemeName == TEXT("v"))
	{
		// Teeth on lip
		VisemeWeights.Add(TEXT("JawOpen"), 0.1f);
		VisemeWeights.Add(TEXT("MouthOpen"), 0.1f);
		VisemeWeights.Add(TEXT("LipPucker"), 0.3f);
	}
	else if (VisemeName == TEXT("a") || VisemeName == TEXT("aa"))
	{
		// Wide open
		VisemeWeights.Add(TEXT("JawOpen"), 0.8f);
		VisemeWeights.Add(TEXT("MouthOpen"), 0.8f);
	}
	else if (VisemeName == TEXT("i") || VisemeName == TEXT("ee"))
	{
		// Wide smile
		VisemeWeights.Add(TEXT("JawOpen"), 0.2f);
		VisemeWeights.Add(TEXT("MouthOpen"), 0.2f);
		VisemeWeights.Add(TEXT("MouthSmile"), 0.6f);
	}
	else if (VisemeName == TEXT("o") || VisemeName == TEXT("oh"))
	{
		// Round
		VisemeWeights.Add(TEXT("JawOpen"), 0.4f);
		VisemeWeights.Add(TEXT("MouthOpen"), 0.4f);
		VisemeWeights.Add(TEXT("LipPucker"), 0.6f);
	}
	else if (VisemeName == TEXT("u") || VisemeName == TEXT("uu"))
	{
		// Very round
		VisemeWeights.Add(TEXT("JawOpen"), 0.3f);
		VisemeWeights.Add(TEXT("MouthOpen"), 0.3f);
		VisemeWeights.Add(TEXT("LipPucker"), 0.8f);
	}
	else
	{
		// Default: slight open
		VisemeWeights.Add(TEXT("JawOpen"), 0.3f);
		VisemeWeights.Add(TEXT("MouthOpen"), 0.3f);
	}

	// Apply blend shape weights
	for (const auto& Pair : VisemeWeights)
	{
		float FinalWeight = Pair.Value * Weight;
		SkeletalMeshComponent->SetMorphTarget(FName(*Pair.Key), FinalWeight, false);
	}
}

FString ULipSyncComponent::PhonemeToViseme(const FString& Phoneme) const
{
	// Convert ARPAbet phonemes to visemes
	// Simplified mapping - in production, use comprehensive phoneme-to-viseme table
	if (Phoneme == TEXT("SIL") || Phoneme == TEXT("SP"))
	{
		return TEXT("silence");
	}
	else if (Phoneme == TEXT("P") || Phoneme == TEXT("B") || Phoneme == TEXT("M"))
	{
		return TEXT("p");
	}
	else if (Phoneme == TEXT("F") || Phoneme == TEXT("V"))
	{
		return TEXT("f");
	}
	else if (Phoneme == TEXT("AA") || Phoneme == TEXT("AH") || Phoneme == TEXT("AO"))
	{
		return TEXT("a");
	}
	else if (Phoneme == TEXT("IY") || Phoneme == TEXT("IH"))
	{
		return TEXT("i");
	}
	else if (Phoneme == TEXT("OW") || Phoneme == TEXT("OY"))
	{
		return TEXT("o");
	}
	else if (Phoneme == TEXT("UW") || Phoneme == TEXT("UH"))
	{
		return TEXT("u");
	}

	return TEXT("a"); // Default viseme
}

FString ULipSyncComponent::SelectPhonemeForEnergy(float NormalizedEnergy) const
{
	if (NormalizedEnergy < 0.05f)
	{
		return TEXT("SIL");
	}
	else if (NormalizedEnergy < 0.2f)
	{
		return TEXT("M");
	}
	else if (NormalizedEnergy < 0.4f)
	{
		return TEXT("AA");
	}
	else if (NormalizedEnergy < 0.7f)
	{
		return TEXT("OH");
	}

	return TEXT("EE");
}

