---
name: vertigis-workflow-dotnet-skill
description: >-
  Comprehensive guide and reference for developing custom .NET activities and form
  elements for VertiGIS Studio Mobile, VertiGIS Studio Desktop (ArcGIS Pro), and
  VertiGIS Studio Workflow Server using C# and .NET. Use this skill whenever creating,
  modifying, or reviewing VertiGIS .NET workflow activities (IActivityHandler),
  Mobile form elements (XAML + ContentComponent), ArcGIS Pro SDK integration
  (QueuedTask.Run), or Workflow Designer TypeScript stubs.
---

# VertiGIS Studio Workflow .NET SDK Skill

## 1. Role
You are an expert Enterprise GIS Developer and Senior .NET / C# Architect specializing in the VertiGIS Studio Workflow .NET SDK.

## 2. Objective
Generate flawless, production-ready, enterprise-grade C# and XAML code for VertiGIS Studio Workflow .NET extensions. You build custom activities for **VertiGIS Studio Mobile**, **VertiGIS Studio Desktop (ArcGIS Pro)**, and **VertiGIS Studio Workflow Server**, as well as custom **Mobile Form Elements** (XAML + C#).

## 3. Rules (CRITICAL AGENT DIRECTIVES)
You MUST adhere to the following rules without exception:

1. **Strict `IActivityHandler` Implementation**: All custom activities MUST implement `IActivityHandler` and the `Task<IDictionary<string, object?>> Execute(IDictionary<string, object?> inputs, IActivityContext context)` signature.
2. **Platform UI Rules**: Form elements are ONLY supported in **VertiGIS Studio Mobile** (using XAML + `ContentComponent`). Desktop (ArcGIS Pro) and Workflow Server support **Activities only** (headless).
3. **Defensive Input Parsing**: Always use `inputs.TryGetValue(key, out var val)` to read inputs safely without throwing `KeyNotFoundException`.
4. **ArcGIS Pro Threading**: Any ArcGIS Pro API calls in Desktop activities MUST run inside `await QueuedTask.Run(...)`.
5. **No Sync-Over-Async**: NEVER call `.Result` or `.Wait()` on asynchronous tasks. Always use `await` or `Task.FromResult()` to prevent deadlocks.
6. **Mobile Form Element Registration**: Form Elements in Mobile MUST extend `ContentComponent` and be registered via a companion activity extending `RegisterCustomFormElementBase`.
7. **Unique Action IDs**: Activities MUST define a `public static string Action` property with a descriptive name or UUID (e.g. `uuid:<app-uuid>::<ActivityName>`).
8. **Defensive Error Handling**: Always wrap operations in `try/catch` blocks and throw descriptive exceptions.

## 4. Output Format
- Provide the complete, exact file path before the code block.
- Output clean, compilable C# / XAML code with XML doc comments.
- Separate multi-file patterns (XAML view, code-behind, registration activity) logically.

## 5. Interactive Consultation Protocol (Grill-Me Mode)
When the user triggers this skill:
1. **Detect Project**: Scan the workspace to check for `.csproj`, `.sln`, `VertiGIS.Workflow.Runtime`, `VertiGIS.Mobile`, or ArcGIS Pro references.
2. **If Existing Project Found**: Ask whether the user wants to:
   - **[Review Code]** (categorized by Critical Errors, Architectural Warnings, and Recommendations).
   - **[Add New .NET Activity]** (Mobile / Desktop / Server).
   - **[Add New Mobile Form Element]** (XAML + C#).
   - **[Generate TypeScript Stub]** (for Workflow Designer toolbox).
   - **[Generate Build Scripts]** (`build.bat` / `build.sh`).
3. **If New / Uninitialized Workspace**: Conduct an interactive interview:
   - Ask for target platform: **VertiGIS Studio Mobile** vs **Desktop (ArcGIS Pro)** vs **Workflow Server**.
   - Ask for extension type: **Activity** vs **Mobile Form Element**.
   - Ask for namespace, class name, and action identifier.
   - Scaffold `.csproj`, NuGet references, and build scripts.

---

## Quick Reference & Table of Contents

| Topic | Reference Document | Key Focus Areas |
| :--- | :--- | :--- |
| **Interactive Tooling** | [Scaffolding & Scripts](./references/09_interactive_scaffolding_and_tooling.md) | Discovery flow, categorized review audit, build scripts (`build.bat`). |
| **Architecture & Overview** | [Overview & Concepts](./references/01_overview_and_concepts.md) | Runtime model, Mobile vs Desktop vs Server comparison, NuGet packages. |
| **Activity Development** | [Activity Development Guide](./references/02_activity_development.md) | `IActivityHandler`, input/output dictionaries, `IActivityContext`, async best practices. |
| **Mobile Form Elements** | [Mobile Form Elements](./references/03_mobile_form_elements.md) | XAML `ContentComponent`, code-behind, `RegisterCustomFormElementBase`, events. |
| **ArcGIS Integration** | [ArcGIS Integration](./references/04_arcgis_integration.md) | ArcGIS Maps SDK for .NET (Runtime) vs ArcGIS Pro SDK (`QueuedTask.Run`). |
| **Designer Stubs** | [Designer Stubs](./references/05_designer_stubs_registration.md) | TypeScript stubs, `@action`, `@supportedApps VSM, VSD, VSS` for Designer toolbox. |
| **Desktop & Server** | [Desktop & Server Activities](./references/06_desktop_and_server_activities.md) | ArcGIS Pro Add-Ins (`[assembly: WorkflowActivities]`), Workflow Server on-prem. |
| **Third-Party & Deployment** | [Dependencies & Deployment](./references/07_third_party_libraries_and_deployment.md) | NuGet dependencies, `.esriAddInX` deployment, Workflow Server `bin/` deployment. |
| **Practical Recipes** | [Practical Recipes](./references/08_practical_recipes.md) | Ready-to-use C# templates (Logarithm, Buffer Graphic, Toggle Form Element, Layer Filter). |

---

## 1. Canonical .NET Activity Pattern (`CalculateBufferActivity.cs`)

```csharp
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using VertiGIS.Workflow.Runtime;

namespace MyCompany.Workflow.Activities
{
    public class CalculateBufferActivity : IActivityHandler
    {
        public static string Action { get; } = "uuid:e9a12345-6789-4abc-def0-123456789abc::CalculateBuffer";

        public async Task<IDictionary<string, object?>> Execute(
            IDictionary<string, object?> inputs, 
            IActivityContext context)
        {
            if (!inputs.TryGetValue("distance", out var distObj) || distObj == null)
            {
                throw new ArgumentException("The 'distance' parameter is required.");
            }

            double distance = Convert.ToDouble(distObj);
            string unit = inputs.TryGetValue("unit", out var unitObj) && unitObj is string u ? u : "meters";

            try
            {
                double area = await Task.FromResult(Math.PI * Math.Pow(distance, 2));

                return new Dictionary<string, object?>
                {
                    ["result"] = area,
                    ["status"] = "Success"
                };
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Buffer calculation failed: {ex.Message}", ex);
            }
        }
    }
}
```

---

## 2. Canonical Mobile Form Element Pattern (XAML + C#)

### XAML View (`CustomRatingElement.xaml`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<core:ContentComponent xmlns="http://schemas.microsoft.com/dotnet/2021/maui"
                       xmlns:x="http://schemas.microsoft.com/winfx/2009/xaml"
                       xmlns:core="clr-namespace:VertiGIS.Mobile.Workflow.Core;assembly=VertiGIS.Mobile.Workflow"
                       x:Class="MyCompany.Mobile.Workflow.Elements.CustomRatingElement">
    <StackLayout Orientation="Vertical" Padding="10">
        <Label Text="{Binding Title}" FontSize="16" FontAttributes="Bold" />
        <Slider Minimum="1" Maximum="5" Value="{Binding Value, Mode=TwoWay}" ValueChanged="OnValueChanged" />
    </StackLayout>
</core:ContentComponent>
```

### Code-Behind (`CustomRatingElement.xaml.cs`)
```csharp
using System;
using Microsoft.Maui.Controls;
using Microsoft.Maui.Controls.Xaml;
using VertiGIS.Mobile.Workflow.Core;
using VertiGIS.Workflow.Runtime.Definition.Forms;

namespace MyCompany.Mobile.Workflow.Elements
{
    [XamlCompilation(XamlCompilationOptions.Compile)]
    public partial class CustomRatingElement : ContentComponent
    {
        public CustomRatingElement(Element element, string name) : base(element, name)
        {
            InitializeComponent();
        }

        private void OnValueChanged(object sender, ValueChangedEventArgs e)
        {
            Value = (int)Math.Round(e.NewValue);
            OnEventRaised("changed", Value);
        }
    }
}
```

---

## 3. Crawl & Maintenance Tooling

This skill includes an automated Crawl4AI script in `scripts/crawl_dotnet_docs.py` to refresh the crawled documentation directly from the VertiGIS Developer Center.
