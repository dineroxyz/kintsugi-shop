# kintsugi-shop

The demo shop that [Kintsugi](https://console-production-f3b9.up.railway.app)
guards: an order service (`services/alpha`) and the pricing service it calls
(`services/beta`), instrumented with Kintsugi's capture library
(`libs/kintsugi_capture`).

## The pull requests in this repository are opened by Kintsugi

When someone presses **Break it** on the
[Live page](https://console-production-f3b9.up.railway.app/live), a bug from
the study corpus is planted in a running copy of this shop. Kintsugi catches
the failure, reproduces it in a sealed copy, has an AI model write a patch,
and deploys it only once the reproduction passes. It then records the repair
here, the way a real team would review it:

* an `incident/...` branch holds the release with the bug, exactly as it ran;
* a pull request from a `kintsugi/fix-...` branch carries the admitted patch
  and the regression test Kintsugi compiled from the failure;
* the pull request links to the signed certificate of the repair.

Nobody on the team wrote these patches. Review them like any other change.

Part of MSc Computer Science research at the University of Lagos by
Abe Oluwaseyi Elizabeth.
