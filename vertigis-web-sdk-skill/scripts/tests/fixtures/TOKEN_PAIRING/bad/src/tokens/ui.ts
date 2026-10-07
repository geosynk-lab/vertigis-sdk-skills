export const UI_TOKENS = {
    surface: {
        primary: "var(--primaryBackground, #ffffff)",
        secondary: "var(--secondaryBackground, #ebebeb)",
    },
    text: {
        primary: "var(--primaryForeground, #323232)",
        secondary: "var(--secondaryForeground, #575757)",
        disabled: "var(--primaryForegroundDisabled, #a1a1a1)",
    },
    accent: {
        primary: "var(--primaryAccent, #1a72c4)",
        light: "var(--primaryAccentLight, #e3eff9)",
        contrastText: "var(--emphasizedButtonForeground, #ffffff)",
    },
    control: {
        itemHover: "var(--itemHoverBackground, #89b8e4)",
    },
    status: {
        errorBg: "var(--alertRedBackground, #b22222)",
        errorFg: "var(--alertRedForeground, #ffffff)",
    },
} as const;
