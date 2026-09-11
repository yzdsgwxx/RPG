using UnrealSharp;
using UnrealSharp.CoreUObject;

namespace RPG;

/// <summary>
/// 资源动态加载辅助。
///
/// 项目约定（见 AGENTS.md 2.5）：
///   1. 资源路径一律用软引用在编辑器里配置：<see cref="TSoftObjectPtr{T}"/> / <see cref="TSoftClassPtr{T}"/>，
///      避免硬引用导致资源常驻内存。
///   2. 运行时按需动态加载：<c>UObject.StaticLoadObject&lt;T&gt;</c> / <c>UObject.StaticLoadClass&lt;T&gt;</c>
///      （对应 UE 的 LoadObject / LoadClass）。
///   3. 路径集中在 DataTable / DataAsset 中，不要在业务代码里散落字符串拼接。
///
/// 用法示例：
///   <code>
///   [UProperty(PropertyFlags.EditDefaultsOnly)]
///   public partial TSoftClassPtr&lt;AActor&gt; EnemyClass { get; set; }
///
///   TSubclassOf&lt;AActor&gt; cls = RPGAssetLoader.LoadClass(EnemyClass);
///   </code>
/// </summary>
public static class RPGAssetLoader
{
    /// <summary>
    /// 软引用取对象：已加载直接返回，未加载则按路径动态加载；软引用为空返回 null。
    /// </summary>
    public static T? Load<T>(TSoftObjectPtr<T> softRef) where T : UObject
    {
        if (softRef.IsNull)
        {
            return null;
        }

        T? loaded = softRef.Object;
        if (loaded != null)
        {
            return loaded;
        }

        return UObject.StaticLoadObject<T>(softRef.SoftObjectPath.ToString());
    }

    /// <summary>
    /// 软类引用取类：按路径动态加载（UMaterial、ACharacter 等蓝图/原生类均适用）。
    /// </summary>
    public static TSubclassOf<T> LoadClass<T>(TSoftClassPtr<T> softClassRef) where T : UObject
    {
        return UObject.StaticLoadClass<T>(softClassRef.SoftObjectPath.ToString());
    }

    /// <summary>按资产路径动态加载对象，例如 "/Game/Mesh/SM_Sword.SM_Sword"。</summary>
    public static T LoadByPath<T>(string assetPath) where T : UObject
    {
        return UObject.StaticLoadObject<T>(assetPath);
    }

    /// <summary>按资产路径动态加载类，例如 "/Game/Blueprint/Actor/BP_Enemy.BP_Enemy_C"。</summary>
    public static TSubclassOf<T> LoadClassByPath<T>(string classPath) where T : UObject
    {
        return UObject.StaticLoadClass<T>(classPath);
    }
}
