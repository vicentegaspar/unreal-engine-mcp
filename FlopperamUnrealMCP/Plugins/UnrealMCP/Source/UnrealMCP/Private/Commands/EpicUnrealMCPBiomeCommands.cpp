#include "Commands/EpicUnrealMCPBiomeCommands.h"
#include "Commands/EpicUnrealMCPCommonUtils.h"
#include "Engine/World.h"
#include "Engine.h"
#include "Editor.h"
#include "Landscape/Landscape.h"
#include "LandscapeInfo.h"
#include "LandscapeComponent.h"
#include "LandscapeLayerInfoObject.h"
#include "LandscapeEditorObject.h"
#include "LandscapeEditorUtils.h"
#include "LandscapeDataAccess.h"
#include "InstancedFoliageActor.h"
#include "FoliageType_InstancedStaticMesh.h"
#include "ProceduralFoliageComponent.h"
#include "ProceduralFoliageSpawner.h"
#include "EditorAssetLibrary.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Factories/LandscapeGrassTypeFactory.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "Misc/DateTime.h"
#include "HAL/PlatformFilemanager.h"
#include "ImageUtils.h"

FEpicUnrealMCPBiomeCommands::FEpicUnrealMCPBiomeCommands()
{
}

TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
    // Landscape generation commands
    if (CommandType == TEXT("create_landscape"))
    {
        return HandleCreateLandscape(Params);
    }
    else if (CommandType == TEXT("generate_heightmap"))
    {
        return HandleGenerateHeightmap(Params);
    }
    else if (CommandType == TEXT("paint_landscape_material"))
    {
        return HandlePaintLandscapeMaterial(Params);
    }
    else if (CommandType == TEXT("create_landscape_layer"))
    {
        return HandleCreateLandscapeLayer(Params);
    }
    // Foliage generation commands
    else if (CommandType == TEXT("spawn_foliage"))
    {
        return HandleSpawnFoliage(Params);
    }
    else if (CommandType == TEXT("create_foliage_type"))
    {
        return HandleCreateFoliageType(Params);
    }
    else if (CommandType == TEXT("setup_procedural_foliage"))
    {
        return HandleSetupProceduralFoliage(Params);
    }
    else if (CommandType == TEXT("paint_foliage"))
    {
        return HandlePaintFoliage(Params);
    }
    // Main biome generation command
    else if (CommandType == TEXT("generate_biome"))
    {
        return HandleGenerateBiome(Params);
    }
    else if (CommandType == TEXT("create_biome_blueprint"))
    {
        return HandleCreateBiomeBlueprint(Params);
    }
    
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown biome command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandleCreateLandscape(const TSharedPtr<FJsonObject>& Params)
{
    // Get parameters
    FVector Location = FVector::ZeroVector;
    if (Params->HasField(TEXT("location")))
    {
        const TArray<TSharedPtr<FJsonValue>>* LocationArray;
        if (Params->TryGetArrayField(TEXT("location"), LocationArray) && LocationArray->Num() >= 3)
        {
            Location.X = (*LocationArray)[0]->AsNumber();
            Location.Y = (*LocationArray)[1]->AsNumber();
            Location.Z = (*LocationArray)[2]->AsNumber();
        }
    }

    int32 ComponentCountX = 8;
    int32 ComponentCountY = 8;
    int32 QuadsPerComponent = 63;
    int32 SubsectionSizeQuads = 31;

    Params->TryGetNumberField(TEXT("component_count_x"), ComponentCountX);
    Params->TryGetNumberField(TEXT("component_count_y"), ComponentCountY);
    Params->TryGetNumberField(TEXT("quads_per_component"), QuadsPerComponent);
    Params->TryGetNumberField(TEXT("subsection_size_quads"), SubsectionSizeQuads);

    // Create landscape
    ALandscape* Landscape = CreateLandscapeActor(Location, ComponentCountX, ComponentCountY, 
                                               QuadsPerComponent, SubsectionSizeQuads);

    if (!Landscape)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create landscape actor"));
    }

    // Return success response
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("status"), TEXT("success"));
    Result->SetStringField(TEXT("landscape_name"), Landscape->GetName());
    Result->SetNumberField(TEXT("size_x"), ComponentCountX * QuadsPerComponent + 1);
    Result->SetNumberField(TEXT("size_y"), ComponentCountY * QuadsPerComponent + 1);
    Result->SetStringField(TEXT("message"), TEXT("Landscape created successfully"));

    return Result;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandleGenerateHeightmap(const TSharedPtr<FJsonObject>& Params)
{
    FString LandscapeName;
    if (!Params->TryGetStringField(TEXT("landscape_name"), LandscapeName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'landscape_name' parameter"));
    }

    // Find landscape actor
    ALandscape* Landscape = nullptr;
    for (TActorIterator<ALandscape> ActorItr(GWorld); ActorItr; ++ActorItr)
    {
        if (ActorItr->GetName() == LandscapeName)
        {
            Landscape = *ActorItr;
            break;
        }
    }

    if (!Landscape)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Landscape not found"));
    }

    // Get heightmap parameters
    const TSharedPtr<FJsonObject>* NoiseSettings = nullptr;
    if (!Params->TryGetObjectField(TEXT("noise_settings"), NoiseSettings))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'noise_settings' parameter"));
    }

    // Get landscape info
    ULandscapeInfo* LandscapeInfo = Landscape->GetLandscapeInfo();
    if (!LandscapeInfo)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get landscape info"));
    }

    FIntRect LandscapeBounds = LandscapeInfo->GetLoadedBounds();
    int32 SizeX = LandscapeBounds.Width() + 1;
    int32 SizeY = LandscapeBounds.Height() + 1;

    // Generate heightmap data
    TArray<uint16> HeightData;
    HeightData.SetNumZeroed(SizeX * SizeY);

    if (!GenerateHeightmapData(HeightData, SizeX, SizeY, *NoiseSettings))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to generate heightmap data"));
    }

    // Apply heightmap to landscape
    FLandscapeEditDataInterface LandscapeEdit(LandscapeInfo);
    LandscapeEdit.SetHeightData(LandscapeBounds.Min.X, LandscapeBounds.Min.Y, 
                               LandscapeBounds.Max.X, LandscapeBounds.Max.Y, 
                               HeightData.GetData(), 0, true);

    // Return success response
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("status"), TEXT("success"));
    Result->SetStringField(TEXT("message"), TEXT("Heightmap applied successfully"));
    Result->SetNumberField(TEXT("heightmap_size_x"), SizeX);
    Result->SetNumberField(TEXT("heightmap_size_y"), SizeY);

    return Result;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandleGenerateBiome(const TSharedPtr<FJsonObject>& Params)
{
    FString BiomeType;
    if (!Params->TryGetStringField(TEXT("biome_type"), BiomeType))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'biome_type' parameter"));
    }

    FVector Location = FVector::ZeroVector;
    if (Params->HasField(TEXT("location")))
    {
        const TArray<TSharedPtr<FJsonValue>>* LocationArray;
        if (Params->TryGetArrayField(TEXT("location"), LocationArray) && LocationArray->Num() >= 3)
        {
            Location.X = (*LocationArray)[0]->AsNumber();
            Location.Y = (*LocationArray)[1]->AsNumber();
            Location.Z = (*LocationArray)[2]->AsNumber();
        }
    }

    int32 BiomeSize = 400000; // 4km default
    Params->TryGetNumberField(TEXT("size"), BiomeSize);

    // Validate size constraints
    if (BiomeSize < 300000 || BiomeSize > 500000)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Biome size must be between 3km and 5km"));
    }

    // Calculate landscape dimensions based on biome size
    int32 ComponentCount = FMath::CeilToInt(BiomeSize / 50900.0f); // Each component is roughly 509m
    ComponentCount = FMath::Clamp(ComponentCount, 4, 32);

    // Create landscape first
    ALandscape* Landscape = CreateLandscapeActor(Location, ComponentCount, ComponentCount, 63, 31);
    if (!Landscape)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create landscape for biome"));
    }

    // Generate biome-specific terrain
    bool BiomeGenerated = false;
    BiomeType = BiomeType.ToLower();

    if (BiomeType == TEXT("desert"))
    {
        BiomeGenerated = GenerateDesertBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("plateau"))
    {
        BiomeGenerated = GeneratePlateauBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("dense_jungle"))
    {
        BiomeGenerated = GenerateJungleBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("riverside"))
    {
        BiomeGenerated = GenerateRiversideBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("tundra"))
    {
        BiomeGenerated = GenerateTundraBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("volcano"))
    {
        BiomeGenerated = GenerateVolcanoBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("marsh"))
    {
        BiomeGenerated = GenerateMarshBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("mushroom_kingdom"))
    {
        BiomeGenerated = GenerateMushroomKingdomBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("crystal_caverns"))
    {
        BiomeGenerated = GenerateCrystalCavernsBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("floating_islands"))
    {
        BiomeGenerated = GenerateFloatingIslandsBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("bioluminescent_forest"))
    {
        BiomeGenerated = GenerateBioluminescentForestBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("mechanical_wasteland"))
    {
        BiomeGenerated = GenerateMechanicalWastelandBiome(Landscape, Params);
    }
    else if (BiomeType == TEXT("coral_reef"))
    {
        BiomeGenerated = GenerateCoralReefBiome(Landscape, Params);
    }
    else
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown biome type: %s"), *BiomeType));
    }

    if (!BiomeGenerated)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to generate %s biome"), *BiomeType));
    }

    // Return success response
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("status"), TEXT("success"));
    Result->SetStringField(TEXT("biome_type"), BiomeType);
    Result->SetStringField(TEXT("landscape_name"), Landscape->GetName());
    Result->SetNumberField(TEXT("biome_size"), BiomeSize);
    Result->SetStringField(TEXT("message"), FString::Printf(TEXT("%s biome generated successfully"), *BiomeType));

    return Result;
}

// Utility function implementations
ALandscape* FEpicUnrealMCPBiomeCommands::CreateLandscapeActor(const FVector& Location, int32 ComponentCountX, int32 ComponentCountY, 
                                                            int32 QuadsPerComponent, int32 SubsectionSizeQuads)
{
    UWorld* World = GWorld;
    if (!World)
    {
        return nullptr;
    }

    // Calculate heightmap size
    int32 SizeX = ComponentCountX * QuadsPerComponent + 1;
    int32 SizeY = ComponentCountY * QuadsPerComponent + 1;

    // Create default flat heightmap
    TArray<uint16> HeightData;
    HeightData.SetNumZeroed(SizeX * SizeY);
    
    // Fill with default height (32768 = 0 elevation)
    for (int32 i = 0; i < HeightData.Num(); i++)
    {
        HeightData[i] = 32768;
    }

    // Import landscape
    TMap<FGuid, TArray<uint16>> HeightmapDataPerLayers;
    TMap<FGuid, TArray<FLandscapeImportLayerInfo>> MaterialLayerDataPerLayer;

    FVector Scale = FVector(100.0f, 100.0f, 100.0f);
    
    ALandscape* Landscape = World->SpawnActor<ALandscape>(Location, FRotator::ZeroRotator);
    if (Landscape)
    {
        Landscape->SetActorLabel(FString::Printf(TEXT("BiomeLandscape_%s"), *FDateTime::Now().ToString()));
        
        // Create landscape with import data
        FLandscapeImportDescriptor ImportDescriptor;
        ImportDescriptor.HeightmapImportResult = ELandscapeImportResult::Success;
        ImportDescriptor.HeightmapFilename = TEXT("");
        ImportDescriptor.HeightmapSize = FIntPoint(SizeX, SizeY);
        ImportDescriptor.Scale = Scale;
        
        ULandscapeInfo* LandscapeInfo = ULandscapeInfo::Create(Landscape, FGuid::NewGuid());
        if (LandscapeInfo)
        {
            Landscape->CreateLandscapeInfo();
            Landscape->Import(FGuid::NewGuid(), 0, 0, SizeX - 1, SizeY - 1, 
                            QuadsPerComponent, SubsectionSizeQuads, HeightData.GetData(), 
                            nullptr, MaterialLayerDataPerLayer, ELandscapeImportAlphamapType::Additive);
        }
    }

    return Landscape;
}

bool FEpicUnrealMCPBiomeCommands::GenerateHeightmapData(TArray<uint16>& HeightData, int32 SizeX, int32 SizeY, 
                                                      const TSharedPtr<FJsonObject>& NoiseSettings)
{
    if (!NoiseSettings.IsValid())
    {
        return false;
    }

    // Get noise parameters
    double Frequency = 0.005;
    double Amplitude = 1.0;
    int32 Octaves = 4;

    NoiseSettings->TryGetNumberField(TEXT("frequency"), Frequency);
    NoiseSettings->TryGetNumberField(TEXT("amplitude"), Amplitude);
    NoiseSettings->TryGetNumberField(TEXT("octaves"), Octaves);

    // Generate heightmap using Perlin noise
    for (int32 Y = 0; Y < SizeY; Y++)
    {
        for (int32 X = 0; X < SizeX; X++)
        {
            float NoiseValue = GeneratePerlinNoise(X, Y, Frequency, Octaves, Amplitude);
            
            // Convert to height value (0-65535 range, 32768 is sea level)
            uint16 HeightValue = FMath::Clamp((int32)(32768 + NoiseValue * 16384), 0, 65535);
            
            HeightData[Y * SizeX + X] = HeightValue;
        }
    }

    return true;
}

float FEpicUnrealMCPBiomeCommands::GeneratePerlinNoise(float X, float Y, float Frequency, int32 Octaves, float Amplitude)
{
    float Result = 0.0f;
    float Freq = Frequency;
    float Amp = Amplitude;

    for (int32 Octave = 0; Octave < Octaves; Octave++)
    {
        Result += FMath::PerlinNoise2D(FVector2D(X * Freq, Y * Freq)) * Amp;
        Freq *= 2.0f;
        Amp *= 0.5f;
    }

    return Result;
}

// Biome-specific generation functions (simplified implementations)
bool FEpicUnrealMCPBiomeCommands::GenerateDesertBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    if (!Landscape)
    {
        return false;
    }

    ULandscapeInfo* LandscapeInfo = Landscape->GetLandscapeInfo();
    if (!LandscapeInfo)
    {
        return false;
    }

    // Generate desert heightmap with dunes
    FIntRect LandscapeBounds = LandscapeInfo->GetLoadedBounds();
    int32 SizeX = LandscapeBounds.Width() + 1;
    int32 SizeY = LandscapeBounds.Height() + 1;

    TArray<uint16> HeightData;
    HeightData.SetNumZeroed(SizeX * SizeY);

    // Create dune patterns
    for (int32 Y = 0; Y < SizeY; Y++)
    {
        for (int32 X = 0; X < SizeX; X++)
        {
            float BaseHeight = 32768; // Sea level
            
            // Add dune noise
            float DuneNoise = GeneratePerlinNoise(X * 0.001f, Y * 0.001f, 0.5f, 2, 0.8f);
            float DetailNoise = GeneratePerlinNoise(X * 0.02f, Y * 0.02f, 1.0f, 6, 0.2f);
            
            float FinalHeight = BaseHeight + (DuneNoise * 8192) + (DetailNoise * 2048);
            HeightData[Y * SizeX + X] = FMath::Clamp((int32)FinalHeight, 0, 65535);
        }
    }

    // Apply heightmap
    FLandscapeEditDataInterface LandscapeEdit(LandscapeInfo);
    LandscapeEdit.SetHeightData(LandscapeBounds.Min.X, LandscapeBounds.Min.Y, 
                               LandscapeBounds.Max.X, LandscapeBounds.Max.Y, 
                               HeightData.GetData(), 0, true);

    return true;
}

bool FEpicUnrealMCPBiomeCommands::GeneratePlateauBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for plateau biome generation
    // Similar pattern to desert but with flat-topped terrain
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateJungleBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for jungle biome generation
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateRiversideBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for riverside biome generation
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateTundraBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for tundra biome generation
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateVolcanoBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for volcano biome generation
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateMarshBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for marsh biome generation
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateMushroomKingdomBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for mushroom kingdom biome generation
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateCrystalCavernsBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for crystal caverns biome generation
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateFloatingIslandsBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for floating islands biome generation
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateBioluminescentForestBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for bioluminescent forest biome generation
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateMechanicalWastelandBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for mechanical wasteland biome generation
    return true;
}

bool FEpicUnrealMCPBiomeCommands::GenerateCoralReefBiome(ALandscape* Landscape, const TSharedPtr<FJsonObject>& BiomeConfig)
{
    // Implementation for coral reef biome generation
    return true;
}

// Placeholder implementations for remaining functions
TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandlePaintLandscapeMaterial(const TSharedPtr<FJsonObject>& Params)
{
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Paint landscape material not yet implemented"));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandleCreateLandscapeLayer(const TSharedPtr<FJsonObject>& Params)
{
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Create landscape layer not yet implemented"));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandleSpawnFoliage(const TSharedPtr<FJsonObject>& Params)
{
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Spawn foliage not yet implemented"));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandleCreateFoliageType(const TSharedPtr<FJsonObject>& Params)
{
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Create foliage type not yet implemented"));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandleSetupProceduralFoliage(const TSharedPtr<FJsonObject>& Params)
{
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Setup procedural foliage not yet implemented"));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandlePaintFoliage(const TSharedPtr<FJsonObject>& Params)
{
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Paint foliage not yet implemented"));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPBiomeCommands::HandleCreateBiomeBlueprint(const TSharedPtr<FJsonObject>& Params)
{
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Create biome blueprint not yet implemented"));
}
