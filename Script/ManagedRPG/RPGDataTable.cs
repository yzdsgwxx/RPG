using UnrealSharp;
using UnrealSharp.Core;
using UnrealSharp.CoreUObject;
using UnrealSharp.Engine;
using UnrealSharp.RPG;

namespace RPG;

/// <summary>
/// DataTable 读取辅助。
///
/// 关键结论（已在本工程编译验证）：
///   UE 要求 DataTable 的行结构必须继承 FTableRowBase（Engine/Classes/Engine/DataTable.h:89）。
///   UnrealSharp 的 C# [UStruct] 会被编译成 UCSScriptStruct（继承 UUserDefinedStruct），
///   编辑器里手工创建的 User Defined Struct 同样是 UUserDefinedStruct —— 两者都不满足
///   这个继承要求，**不能**用作 DataTable 的行结构。
///
///   因此行结构要在 C++ 侧定义（见 Source/RPG/RPGTableRows.h 的 FRPGItemRow）。
///   UnrealSharp 会为它生成 C# 类型 UnrealSharp.RPG.FRPGItemRow（实现 MarshalledStruct&lt;T&gt;），
///   于是就能在 C# 里直接 FindRow / TryFindRow 读取。注意命名映射：
///     C++ FRPGItemRow  →  C# 类型 FRPGItemRow（保留 F）  →  UE 结构体名 RPGItemRow（去掉首字符 F）
///
/// 用法：
///   <code>
///   [UProperty(PropertyFlags.EditDefaultsOnly)]
///   public partial TSoftObjectPtr&lt;UDataTable&gt; ItemTable { get; set; }
///
///   if (RPGDataTable.TryGetRow(ItemTable, new FName("Sword_01"), out FRPGItemRow row))
///   {
///       int stack = row.MaxStack;                       // 直接读字段
///       UTexture2D? icon = RPGAssetLoader.Load(row.Icon); // 软引用按需动态加载
///   }
///   </code>
/// </summary>
public static class RPGDataTable
{
    /// <summary>
    /// 安全读取一行：表资产按软引用动态加载，行不存在时返回 false。
    /// </summary>
    public static bool TryGetRow<T>(TSoftObjectPtr<UDataTable> tableRef, FName rowName, out T row)
        where T : MarshalledStruct<T>
    {
        row = default!;

        UDataTable? table = RPGAssetLoader.Load(tableRef);
        if (table == null || !table.HasRow(rowName))
        {
            return false;
        }

        // FindRow<T> 的 T 在本项目里恒为结构体（MarshalledStruct），不会出现 null 赋值；
        // UnrealSharp 的泛型约束未限定 struct，编译器因此报 CS8601，这里精确抑制。
#pragma warning disable CS8601
        row = table.FindRow<T>(rowName);
#pragma warning restore CS8601
        return true;
    }

    /// <summary>
    /// 从已加载的表里读取一行（调用方自行保证表非空）。
    /// </summary>
    public static T GetRow<T>(UDataTable table, FName rowName) where T : MarshalledStruct<T>
    {
        return table.FindRow<T>(rowName);
    }

    /// <summary>
    /// 遍历整张表。回调拿到行名与该行数据。
    /// </summary>
    public static void ForEachRow<T>(TSoftObjectPtr<UDataTable> tableRef, Action<FName, T> action)
        where T : MarshalledStruct<T>
    {
        UDataTable? table = RPGAssetLoader.Load(tableRef);
        if (table == null)
        {
            return;
        }

        table.ForEachRow(action);
    }
}
