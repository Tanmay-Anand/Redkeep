# Redkeep logo

Colours: ink `#262626`, light ink `#F2F2F0`, light background `#FAFAF8`, dark background `#18181A`.
Typeface: Space Grotesk Medium (500), letter-spacing -0.04em. The wordmark in these files is converted to outlines, so no font is needed.

- `svg/` - vector masters. `-dark` = dark ink for light backgrounds, `-light` = light ink for dark backgrounds.
- `png/transparent/` - lockup (1200/2400/4800 px wide) and mark (256/512/1024 px square) on transparent backgrounds.
- `png/solid/` - the same on the light (`on-light`) or dark (`on-dark`) brand background.
- `favicons/` - drop into your web root and add to `<head>`:

```html
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
```

`favicon.svg` switches to light ink in dark mode; the .ico/.png favicons are dark ink on transparent.
