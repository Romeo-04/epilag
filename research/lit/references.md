# References

Keys are used in `feature_evidence.csv` and `rrl_matrix.csv`.

**Verified** means the source page was opened on 2026-11-16 and the claim used here was seen on it: the full text on PubMed Central or the publisher, or the abstract through Europe PMC. Where only part of a claim could be seen, the note says so.

## Philippines

- **carvajal2018**: Carvajal TM, Viacrusis KM, Hernandez LFT, Ho HT, Amalin DM, Watanabe K. (2018). Machine learning methods reveal the temporal pattern of dengue incidence using meteorological factors in metropolitan Manila, Philippines. *BMC Infectious Diseases*, 18, 183. https://doi.org/10.1186/s12879-018-3066-0 (PMC5905126). **Verified** (PMC full text, first part):
  - Weekly data 2009–2013, test year 2013.
  - Compared GAM, SARIMAX, random forest and gradient boosting.
  - Random forest with lagged inputs was best, and relative humidity was the top weather factor.
  - Cross-correlation lags: humidity 4 weeks, rain 5, minimum temperature 13, mean 17, maximum 18, SOI 20.
  - The error values (random forest MAE 0.15 against SARIMAX 0.27) were seen only in a summary of the later part of the page.
- **olana2025**: Olana KOA, Poprom N, Siewchaisakul P, Punyapornwithaya V, Thongprachum A. (2025). Spatial distribution analysis and comparative forecasting of dengue resurgence in the Philippines (2025–2027): A nationwide study. *Transboundary and Emerging Diseases*, 2025, 7480710. https://doi.org/10.1155/tbed/7480710 (PMC12543447). **Verified** (PMC full text):
  - Monthly data 2017–2024, trained to Dec 2023, tested on 2024.
  - Compared SARIMA, NNAR, random forest, LSTM, TBATS and Prophet, scored by MAE, MAPE, MASE and RMSE.
  - NNAR was best. Confidence intervals were shown.
  - Seasonal peaks fall in July to September.
  - The background notes random forest's main limitation: it cannot predict beyond the range of its training data.
- **iguchi2018**: Iguchi JA, Seposo XT, Honda Y. (2018). Meteorological factors affecting dengue incidence in Davao, Philippines. *BMC Public Health*, 18, 629. https://doi.org/10.1186/s12889-018-5532-4 (PMC5952851). **Verified** (PMC):
  - Weekly data 2011–2015, quasi-Poisson distributed-lag non-linear model with a maximum lag of 12 weeks.
  - Rain at 32 mm had RR 1.67 (95% CI 1.07–2.62), and risk rose with dew point.
  - Mean temperature of 26 °C had RR 1.96 (95% CI 0.47–8.15), while 27–31 °C had lower RR.
- **seposo2023**: Seposo X, Valenzuela S, Apostol GL. (2023). Socio-economic factors and its influence on the association between temperature and dengue incidence in 61 provinces of the Philippines, 2010–2019. *PLOS Neglected Tropical Diseases*, 17(10), e0011700. https://doi.org/10.1371/journal.pntd.0011700 (PMC10621993). **Verified** (PMC):
  - GAMM with a distributed-lag model, maximum lag 18 weeks, ERA5-Land temperature.
  - The risk curve is an inverted U: it rises from 15.8 °C, peaks at 27.5 °C, then declines.
  - Provinces with higher population density showed higher risk at the upper temperature range.
- **buczak2014**: Buczak AL, Baugher B, Babin SM, Ramac-Thomas LC, Guven E, Elbert Y, et al. (2014). Prediction of high incidence of dengue in the Philippines. *PLOS Neglected Tropical Diseases*, 8(4), e2771. https://doi.org/10.1371/journal.pntd.0002771 (PMC3983113). **Verified** (PMC):
  - Province level, weekly, predicting high or low incidence 4 weeks ahead with fuzzy association rules.
  - Data 2003–2011, tested on data not used for development.
  - The high-incidence threshold is the mean plus 1.5 SD.
  - Inputs include rainfall, land surface temperature, SOI, sea surface temperature anomaly and altitude.
  - F0.5 model: PPV 0.780, sensitivity 0.547, specificity 0.978.
- **sumi2017**: Sumi A, Telan EFO, Chagan-Yasutan H, Piolo MB, Hattori T, Kobayashi N. (2017). Effect of temperature, relative humidity and rainfall on dengue fever and leptospirosis infections in Manila, the Philippines. *Epidemiology and Infection*, 145(1), 78–86. https://doi.org/10.1017/S095026881600203X (PMC9507329). **Verified** (Cambridge and PMC):
  - One hospital in Manila, weekly, 2013–2014.
  - Dengue was related to rain over the prior 6–7 weeks.
  - Fitted yearly cycles of humidity, rain and temperature lead dengue by 1, 2 and 4 months.
- **xu2020**: Xu Z, Bambrick H, Yakob L, Devine G, Frentiu FD, Villanueva Salazar F, Bonsato R, Hu W. (2020). High relative humidity might trigger the occurrence of the second seasonal peak of dengue in the Philippines. *Science of the Total Environment*, 708, 134849. https://doi.org/10.1016/j.scitotenv.2019.134849. **Verified** (Europe PMC abstract):
  - Monthly data 2008–2017, 17 regions and 19 provinces.
  - The temperature association is J-shaped or an inverted V; rain and humidity associations differ by province.
  - Relative humidity was the only factor linked to the second seasonal peak (OR 1.144, threshold 77%).
- **sy2026**: Sy AK, Biggs J, Chowdhury SK, Quinones MA, Salazar FV, Jones-Warner W, et al. (2026). The impact of elevation and population density on dengue incidence and force of infection across the Philippines: Implications for climate-adapted surveillance. *PLOS Neglected Tropical Diseases*, 20(5), e0014356. https://doi.org/10.1371/journal.pntd.0014356 (PMC13229340). **Verified** (Europe PMC abstract):
  - Nationwide, 2013–2019, 1.1 million cases plus seroprevalence in 22,270 people.
  - Elevation and density were associated with force of infection, but not with reported incidence.
  - Urban low-elevation barangays had the highest force of infection, at 13.2%.
  - Not to be confused with PMC8898531, which is edillo2022 below.
- **eligado2026**: Eligado AA, Hasegawa T, Hattori Y, Nakamura K. (2026). Advancing outbreak detection: Hybridizing machine learning with wavelets for weekly dengue case forecasting. *PLOS Neglected Tropical Diseases*, 20(7), e0014444. https://doi.org/10.1371/journal.pntd.0014444 (PMC13349185). **Verified** (Europe PMC abstract):
  - Quezon City, weekly, 2012–2022.
  - The DWT-SARMA-LSTM model had a MAPE of 12.4%, against 25.8% for DWT-SARMA.
  - Model-derived alert thresholds were compared with the 3-year moving-mean threshold, which was skewed by pre-pandemic data.
- **edillo2022**: Edillo F, Ymbong RR, Bolneo AA, Hernandez RJ, Fuentes BL, Cortes G, et al. (2022). Temperature, season, and latitude influence development-related phenotypes of Philippine *Aedes aegypti*. *Parasites & Vectors*, 15, 74. https://doi.org/10.1186/s13071-022-05186-x (PMC8898531). **Verified** (PMC and Europe PMC):
  - A laboratory study of Philippine mosquito eggs, with lowland defined as below 100 m.
  - Altitude had no significant main effect on the egg traits; temperature, season and island did.
- **pelitro2026**: Pelitro KJ, et al. (2026). Weekly dengue incidence linked to satellite rainfall at city, regional, and country scales (v1.0.0) [Data set]. Zenodo. https://zenodo.org/records/19448695. The data source for the region and QC panel; cited in the README and not re-checked here.
- **undurraga2017**: Undurraga EA, Edillo FE, Erasmo JNV, Alera MTP, Yoon IK, Largo FM, Shepard DS. (2017). Disease burden of dengue in the Philippines: Adjusting for underreporting by comparing active and passive dengue surveillance in Punta Princesa, Cebu City. *American Journal of Tropical Medicine and Hygiene*, 96(4), 887–898. https://doi.org/10.4269/ajtmh.16-0488. **Verified** (Europe PMC record).
- **doh2019epidemic**: Andrade JI. (2019, August 7). DOH declares national dengue epidemic. *Philippine Daily Inquirer*. https://newsinfo.inquirer.net/1151103/doh-declares-national-dengue-epidemic. **Verified** (article page):
  - The DOH declared a national dengue epidemic on Tuesday, 6 August 2019, three weeks after a national dengue alert.
  - 146,062 cases were recorded from 1 January to 20 July, 98% more than the same period of 2018.

## Southeast Asia and landmark work

- **mordecai2017**: Mordecai EA, Cohen JM, Evans MV, Gudapati P, Johnson LR, et al. (2017). Detecting the impact of temperature on transmission of Zika, dengue, and chikungunya using mechanistic models. *PLOS Neglected Tropical Diseases*, 11(4), e0005568. https://doi.org/10.1371/journal.pntd.0005568. **Verified** (PLOS full text):
  - Transmission occurs at 18–34 °C and peaks at 26–29 °C.
  - For *Ae. aegypti*, transmission peaks at 29.1 °C and drops to zero below 17.8 °C and above 34.6 °C.
  - Validation used the mean temperature 10 weeks before the reporting week.
- **liuhelmersson2014**: Liu-Helmersson J, Stenlund H, Wilder-Smith A, Rocklöv J. (2014). Vectorial capacity of *Aedes aegypti*: Effects of temperature and implications for global dengue epidemic potential. *PLOS ONE*, 9(3), e89783. https://doi.org/10.1371/journal.pone.0089783. **Verified** (Europe PMC abstract):
  - Epidemic potential peaks at a mean of 29.3 °C when the daily range is 0.
  - Near 29 °C, a small daily range raises epidemic potential and a large one lowers it.
- **vanpanhuis2015**: van Panhuis WG, Choisy M, Xiong X, Chok NS, Akarasewi P, Iamsirithaworn S, et al. (2015). Region-wide synchrony and traveling waves of dengue across eight countries in Southeast Asia. *PNAS*, 112(42), 13069–13074. https://doi.org/10.1073/pnas.1501375112 (PMC4620875). **Verified** (PMC):
  - 273 provinces, monthly data up to 18 years.
  - Multiannual cycles (2–5 years) were highly coherent with the Oceanic Niño Index.
  - Synchrony rose by 0.029 per 1 °C.
- **ith2025**: Ith S, Seposo X, Phy V, Tantrakarnapa K, Apostol GLC, Dhewantara PW, et al. (2025). Extreme weather events and dengue in Southeast Asia: A regionally-representative analysis of 291 locations from 1998 to 2021. *PLOS Neglected Tropical Diseases*, 19(9), e0012649. https://doi.org/10.1371/journal.pntd.0012649. **Verified** (Europe PMC abstract):
  - Monthly data from 8 countries.
  - Fewer than 12 heatwave days a month raised risk after a 2-month lag, peaking at 7 days (RR 1.28).
  - Drought raised risk (RR 1.85); extremely wet conditions lowered it (RR 0.89).
- **lowe2014**: Lowe R, Barcellos C, Coelho CAS, Bailey TC, Coelho GE, Graham R, et al. (2014). Dengue outlook for the World Cup in Brazil: an early warning model framework driven by real-time seasonal climate forecasts. *Lancet Infectious Diseases*, 14(7), 619–626. https://doi.org/10.1016/S1473-3099(14)70781-9 (PMID 24841859). **Verified** (Europe PMC abstract):
  - 553 microregions, with probabilistic warnings 3 months ahead.
  - Alert thresholds were tuned on June 2000–2013.
- **shi2016**: Shi Y, Liu X, Kok SY, Rajarethinam J, Liang S, Yap G, et al. (2016). Three-month real-time dengue forecast models: An early warning system for outbreak alerts and policy decision support in Singapore. *Environmental Health Perspectives*, 124(9), 1369–1375. https://doi.org/10.1289/ehp.1509981 (PMC5010413). **Verified** (PMC):
  - Weekly forecasts 1–12 weeks ahead, with LASSO against SARIMA and stepwise regression.
  - MAPE at 3 months: 24% for LASSO, against 29% for SARIMA.
  - 95% intervals were given. The models were trained on 2001–2010, validated on 2011–2012 and applied to 2013.
  - Recent cases at lags of 1–5 weeks helped. Absolute humidity over the last month predicted cases 4–5 weeks ahead.
- **tuan2024**: Tuan DA. (2024). Leveraging climate data for dengue forecasting in Ba Ria Vung Tau Province, Vietnam: An advanced machine learning approach. *Tropical Medicine and Infectious Disease*, 9(10), 250. https://doi.org/10.3390/tropicalmed9100250 (PMC11511084; a correction exists at PMC12115829). **Verified, with a caveat** (PMC):
  - Weekly data 2003–2022, with climate lagged 2–20 weeks.
  - The abstract names negative binomial regression best. The results table, seen only in a summary, shows SARIMAX #2 with a lower MAE (17.0 against 21.4).
  - The negative binomial dispersion was tuned on the test set.
- **colongonzalez2021**: Colón-González FJ, Soares Bastos L, Hofmann B, Hopkin A, Harpham Q, Crocker T, et al. (2021). Probabilistic seasonal dengue forecasting in Vietnam: A modelling study using superensembles. *PLOS Medicine*, 18(3), e1003542. https://doi.org/10.1371/journal.pmed.1003542. **Verified** (PLOS, abstract):
  - 63 provinces, monthly, 1–6 months ahead.
  - The superensemble beat a seasonal-average baseline 1–3 months ahead, but not 4–6 months ahead.
  - Outbreak detection was 69% for the superensemble, against 54.5% for the baseline.
- **johansson2019**: Johansson MA, Apfeldorf KM, Dobson S, Devita J, Buczak AL, Baugher B, et al. (2019). An open challenge to advance probabilistic forecasting for dengue epidemics. *PNAS*, 116(48), 24268–24274. https://doi.org/10.1073/pnas.1909865116 (PMC6883829). **Partly verified**:
  - Seen on the page: 16 teams, 8 years, Peru and Puerto Rico.
  - Seen only in a page summary, so **unverified**: ensembles beat single models, and models using climate data scored lower.
- **rahman2025**: Rahman MS, Amrin M, Bokkor Shiddik MA. (2025). Dengue early warning system and outbreak prediction tool in Bangladesh using interpretable tree-based machine learning model. *Health Science Reports*, 8(5), e70726. https://doi.org/10.1002/hsr2.70726. **Verified** (Europe PMC abstract):
  - Compared random forest, XGBoost and LightGBM, with SHAP for interpretation.
  - Data 2000–2021.
  - Found non-linear temperature thresholds, including a mean of 27 °C.

## Methods

- **ke2017**: Ke G, Meng Q, Finley T, Wang T, Chen W, Ma W, Ye Q, Liu T-Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems 30*. https://papers.nips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html. **Verified** (NeurIPS page): trains up to 20 times faster than conventional gradient boosting with about the same accuracy.
- **romano2019**: Romano Y, Patterson E, Candès E. (2019). Conformalized quantile regression. *Advances in Neural Information Processing Systems 32*. https://arxiv.org/abs/1905.03222. **Verified** (arXiv page title).
- **bowman2016**: Bowman LR, Donegan S, McCall PJ. (2016). Is dengue vector control deficient in effectiveness or evidence?: Systematic review and meta-analysis. *PLOS Neglected Tropical Diseases*, 10(3), e0004551. https://doi.org/10.1371/journal.pntd.0004551. **Verified** (Europe PMC record).
- **makridakis2022**: Makridakis S, Spiliotis E, Assimakopoulos V. (2022). M5 accuracy competition: Results, findings, and conclusions. *International Journal of Forecasting*, 38(4), 1346–1364. https://doi.org/10.1016/j.ijforecast.2021.11.013. **Unverified**: the publisher page blocked automated access. It is the usual citation for LightGBM winning a large forecasting competition; don't use it until someone opens it.
- **senson2026**: Senson et al. (2026), *SciEnggJ* special issue: machine learning with weather for dengue in Quezon City. Found in search results only. **Unverified**: no Europe PMC record found under that author on 2026-11-16, and the page has not been opened. If confirmed, this would be the closest local comparison.
- **mandaue_elev**: Mandaue City study of dengue against elevation and slope, https://publish.mersin.edu.tr/index.php/igd/article/view/1262. **Unverified**: the site did not resolve.
