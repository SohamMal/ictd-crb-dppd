// SOURCE: pasted by Soham on 2026-10-07 from
// https://code.earthengine.google.com/822858cf9574871971b0ac482e6b8982 (GEE project ictd-507010).
// This version filters the 45 "clean" 2011 tehsils; the variant used for the remaining
// villages (exports punjab_ci_villages_{yr}.csv) is not in the repo.
// Review notes: sub_journeys/2_Stage2_Determine_Positive_Deviants/2.2_Homogeneous_Grouping/task_cropping_intensity.md
//
// Punjab tehsil-level Cropping Intensity -- v2
// Multiplier formula (matches the reference doc):
//   CI = 100 * (1*A1 + 2*A2 + 3*A3) / (A1 + A2 + A3)
// where A1/A2/A3 = pixels cropped exactly once / twice / three times in the ag. year.
// Run first on the 45 "clean" 2011=current tehsils (1:1 in the bridge mapping) as a check
// before extending to village-level rollup for the other 52.

// ---------- 1. SETTINGS ----------
// The 45 clean (2011 tehsil == current tehsil) pc11_sd_id values, from the bridge mapping.
// IMPORTANT: pc11_sd_id in shrug_villages is a STRING, zero-padded to 5 digits (e.g. "00200"),
// not a number -- confirmed from the asset's Feature table. This was the actual cause of the
// empty exports: a numeric filter list never matches a string property.
var CLEAN_45_PC11_IDS = ['00200', '00201', '00204', '00205', '00206', '00207', '00208', '00210',
  '00211', '00215', '00216', '00217', '00219', '00220', '00222', '00223', '00224', '00225', '00226',
  '00227', '00228', '00229', '00230', '00231', '00232', '00239', '00240', '00241', '00243', '00245',
  '00248', '00250', '00251', '00252', '00257', '00258', '00261', '00262', '00263', '00264', '00266',
  '00270', '00273', '00274', '00276'];

// No separate tehsil-polygon asset exists (only shrug_villages under ictd-507010), and none is needed:
// SHRUG villages already carry pc11_sd_id, so we run reduceRegions per VILLAGE and sum up to tehsil
// level in Python afterward. This is also exactly the export the other 52 tehsils will need later,
// so this script generalizes -- just widen or drop the pc11_sd_id filter when you get there.
var UNITS = ee.FeatureCollection('projects/ictd-507010/assets/shrug/shrug_villages')
  .filter(ee.Filter.inList('pc11_sd_id', CLEAN_45_PC11_IDS));
var ID_FIELDS = ['pc11_tv_id', 'pc11_sd_id']; // village id + 2011 tehsil id; sum by pc11_sd_id after export
var AG_YEARS = [2022, 2023, 2024];
var SCALE = 10;

// Peak / trough / amplitude thresholds from the reference doc
var PEAK_MIN = 0.475;     // midpoint of the 0.45-0.50 "active crop" band; tune after first look at results
var TROUGH_MAX = 0.225;   // midpoint of the 0.20-0.25 "inter-crop base" band
var AMPLITUDE_MIN = 0.20; // seasonal peak must rise this much above the pre-season trough to count as its own crop

var REGION = UNITS.geometry().bounds();

// ---------- 2. CROPLAND MASK ----------
var cropland = ee.Image('ESA/WorldCover/v200/2021').select('Map').eq(40);

// ---------- 3. CLOUD-MASKED NDVI COLLECTION ----------
function ndviCollection(start, end) {
  return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterDate(start, end)
    .filterBounds(REGION)
    .map(function (img) {
      var scl = img.select('SCL');
      var clear = scl.eq(2).or(scl.eq(4)).or(scl.eq(5)).or(scl.eq(6)).or(scl.eq(7));
      return img.normalizedDifference(['B8', 'B4']).rename('ndvi').updateMask(clear);
    });
}

// ---------- 4. SEASON WINDOWS (agricultural year starting June y) ----------
function seasonWindows(y) {
  return {
    kharif: [y + '-07-01', y + '-10-31'],
    rabi: [y + '-12-01', (y + 1) + '-03-31'],
    zaid: [(y + 1) + '-04-15', (y + 1) + '-06-15']
  };
}

// Safe percentile reduce: always returns a properly-masked 1-band image, even if this date/region
// window happens to contain zero clear Sentinel-2 observations. Without this guard, an empty
// collection's .reduce() returns an image with 0 bands, which crashes any later .lte()/.gte() against
// it with "Image.lte: If one image has no bands, the other must also have no bands." (EE error code 3).
function safeNdviPercentile(start, end, pct) {
  var col = ndviCollection(start, end);
  return ee.Image(ee.Algorithms.If(
    col.size().gt(0),
    col.reduce(ee.Reducer.percentile([pct])).rename('ndvi'),
    ee.Image(0).rename('ndvi').selfMask() // fully masked -> unmask(0) below treats it as "not cropped"
  ));
}

function preSeasonTrough(seasonStart) {
  var end = ee.Date(seasonStart);
  var start = end.advance(-25, 'day');
  return safeNdviPercentile(start, end, 10); // p10 = robust "base" estimate
}

function seasonFlag(seasonStart, seasonEnd) {
  var peak = safeNdviPercentile(seasonStart, seasonEnd, 90);
  var trough = preSeasonTrough(seasonStart);
  var isPeak = peak.gte(PEAK_MIN);
  var isTroughLow = trough.lte(TROUGH_MAX);
  var hasAmplitude = peak.subtract(trough).gte(AMPLITUDE_MIN);
  return isPeak.and(isTroughLow.or(hasAmplitude)).unmask(0);
  // isTroughLow OR hasAmplitude: accept if the pre-season baseline was already low (clean fallow gap),
  // OR the rise itself was big enough even if the baseline reducer had a noisy/missing trough.
}

// ---------- 5. ONE AGRICULTURAL YEAR -> crop-count image (0,1,2,3) ----------
function yearImage(y) {
  var w = seasonWindows(y);
  var kharif = seasonFlag(w.kharif[0], w.kharif[1]);
  var rabi = seasonFlag(w.rabi[0], w.rabi[1]);
  var zaid = seasonFlag(w.zaid[0], w.zaid[1]);

  var cropCount = kharif.add(rabi).add(zaid).updateMask(cropland); // 0,1,2, or 3 per pixel

  var isA1 = cropCount.eq(1);
  var isA2 = cropCount.eq(2);
  var isA3 = cropCount.eq(3);

  return ee.Image.cat([isA1, isA2, isA3])
    .rename(['A1', 'A2', 'A3'])
    .updateMask(cropland);
}

// ---------- 6. SUM PIXEL COUNTS PER TEHSIL AND EXPORT ----------
// Sum A1/A2/A3 counts per tehsil, per year -- compute the CI ratio AFTER export (in Python/Sheets),
// not inside GEE, so a partial/failed export doesn't silently corrupt a divide.
var COLUMNS = ID_FIELDS.concat(['ag_year', 'A1', 'A2', 'A3']);

print('village count:', UNITS.size());

// ~6,096 villages sit inside the 45 clean tehsils. reduceRegions over that many polygons at 10m can be
// slow or time out as one task. If a year's export stalls in the Tasks tab, split UNITS by district
// (filter on the village layer's district field) and run/export each district separately, then
// concatenate the CSVs before the Python step below.
AG_YEARS.forEach(function (y) {
  var sums = yearImage(y)
    .reduceRegions({
      collection: UNITS,
      reducer: ee.Reducer.sum(),
      scale: SCALE,
      tileScale: 8
    })
    .map(function (f) { return f.set('ag_year', y); });

  Export.table.toDrive({
    collection: sums,
    description: 'punjab_ci_clean45_villages_' + y,
    fileFormat: 'CSV',
    selectors: COLUMNS
  });
});

// ---------- After download: roll villages up to tehsil, THEN compute CI, in Python ----------
// tehsil = df.groupby('pc11_sd_id')[['A1','A2','A3']].sum()   -- sum village pixel counts per tehsil
// (if combining multiple years, sum across ag_year here too, before dividing)
// tehsil['CI'] = 100 * (tehsil.A1 + 2*tehsil.A2 + 3*tehsil.A3) / (tehsil.A1 + tehsil.A2 + tehsil.A3)
// Never average village-level or year-level CI percentages directly -- always sum pixel counts first.
