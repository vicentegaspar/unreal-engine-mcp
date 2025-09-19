#pragma once

#include "CoreMinimal.h"
#include "Json.h"
#include "Engine/World.h"
#include "Landscape/Landscape.h"
#include "LandscapeInfo.h"
#include "LandscapeComponent.h"
#include "LandscapeLayerInfoObject.h"
#include "FoliageType.h"
#include "InstancedFoliageActor.h"
#include "ProceduralFoliageComponent.h"
#include "ProceduralFoliageSpawner.h"

/**
 * Handler for biome generation commands including landscape creation,
 * material painting, and procedural foliage placement
 */
class UNREALMCP_API FEpicUnrealMCPBiomeCommands
{
public:
    FEpicUnrealMCPBiomeCommands();

    // Main command handler
    TSharedPtr<FJsonObject> HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params);

private:
    // Landscape generation commands
    TSharedPtr<FJsonObject> HandleCreateLandscape(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleGenerateHeightmap(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandlePaintLandscapeMaterial(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleCreateLandscapeLayer(const TSharedPtr<FJsonObject>& Params);

    // Foliage generation commands
    TSharedPtr<FJsonObject> HandleSpawnFoliage(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleCreateFoliageType(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleSetupProceduralFoliage(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandlePaintFoliage(const TSharedPtr<FJsonObject>& Params);

    // Biome generation commands
    TSharedPtr<FJsonObject> HandleGenerateBiome(const TSharedPtr<FJsonObject>& Params);
    TSharedPtr<FJsonObject> HandleCreateBiomeBlueprint(const TSharedPtr<FJsonObject>& Params);

    // Utility functions
    ALandscape* CreateLandscapeActor(const FVector& Location, int32 ComponentCountX, int32 ComponentCountY, 
                                   int32 QuadsPerComponent, int32 SubsectionSizeQuads);
    bool GenerateHeightmapData(TArray<uint16>& HeightData, int32 SizeX, int32 SizeY, 
                             const TSharedPtr<FJsonObject>& NoiseSettings);
    bool ApplyNoiseLayers(TArray<uint16>& HeightData, int32 SizeX, int32 SizeY, 
                        const TArray<TSharedPtr<FJsonValue>>& NoiseLayers);
    bool PaintLandscapeLayer(ALandscape* Landscape, const FString& LayerName, 
                           const TArray<uint8>& WeightData, int32 SizeX, int32 SizeY);
    
    AInstancedFoliageActor* GetOrCreateFoliageActor(UWorld* World);
    bool SpawnFoliageInstances(AInstancedFoliageActor* FoliageActor, UFoliageType* FoliageType,
                             const TArray<FVector>& Locations, const TArray<FVector>& Scales,
                             const TArray<FRotator>& Rotations);
    TArray<FVector> GenerateFoliageLocations(ALandscape* Landscape, const TSharedPtr<FJsonObject>& FoliageConfig,
                                           int32 Count);
    
    // Noise generation helpers
    float GeneratePerlinNoise(float X, float Y, float Frequency, int32 Octaves, float Amplitude);
    float GenerateRidgedNoise(float X, float Y, float Frequency, int32 Octaves);
    float GenerateBillowNoise(float X, float Y, float Frequency, int32 Octaves);
    
    // Biome-specific generation
    bool GenerateDesertBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GeneratePlateauBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateJungleBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateRiversideBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateTundraBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateVolcanoBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateMarshBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateMushroomKingdomBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateCrystalCavernsBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateFloatingIslandsBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateBioluminescentForestBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateMechanicalWastelandBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
    bool GenerateCoralReefBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig);
};
