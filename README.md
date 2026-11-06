# kyoto-autumn · 京都で、紅葉デート

Our Kyoto itinerary site, 13–15 Nov 2026.

- `index.html`: the whole site
- `three.min.js`: the 3D engine (three.js r128)
- `foliage.json`: the latest Keihan momiji status, updated by the bot
- `.github/workflows/momiji.yml`: checks Keihan and redeploys the site
- `scripts/update_foliage.py`: reads Keihan's report

The weather loads live from Open-Meteo each time the page opens. The momiji
check runs on Tuesdays and Fridays (Keihan's update days) and once a day
otherwise. If Keihan's page ever changes, the check keeps the last good data.

To run the check by hand: Actions → "Momiji check and deploy" → Run workflow.
