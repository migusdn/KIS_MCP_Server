# KIS MCP 사용 가능 API 목록

이 문서는 현재 MCP 서버의 `call-kis-api` 도구로 호출할 수 있는 KIS REST API 카탈로그입니다. 총 `166`개 API를 제공합니다.

## 사용 방법

1. `list-kis-api-specs`로 그룹이나 검색어 기준 API를 찾습니다.
2. `get-kis-api-spec`로 필요한 파라미터와 TR_ID 후보를 확인합니다.
3. `call-kis-api`에 `group`, `api_type`, `params`를 전달해 호출합니다.

주문/정정/취소처럼 계좌 상태를 바꾸는 API는 기본적으로 차단됩니다. 의도적으로 사용할 때만 `KIS_ENABLE_TRADING=true`를 설정하세요.

## 그룹 요약

| 그룹 | 설명 | API 수 |
|---|---|---:|
| `auth` | 인증 | 2 |
| `domestic_bond` | 국내채권 | 14 |
| `domestic_futureoption` | 국내선물옵션 | 20 |
| `domestic_stock` | 국내주식 | 74 |
| `elw` | ELW | 1 |
| `etfetn` | ETF/ETN | 2 |
| `overseas_futureoption` | 해외선물옵션 | 19 |
| `overseas_stock` | 해외주식 | 34 |

## 전체 API

### 인증 (`auth`)

| API ID | 이름 | 메서드 | 경로 | TR_ID | 필수 파라미터 |
|---|---|---|---|---|---|
| `auth_token` | 접근토큰발급(P) | `POST` | `/oauth2/tokenP` | - | `appkey`<br>`appsecret`<br>`grant_type` |
| `auth_ws_token` | 실시간 (웹소켓) 접속키 발급 | `POST` | `/oauth2/Approval` | - | `appkey`<br>`appsecret`<br>`grant_type` |

### 국내채권 (`domestic_bond`)

| API ID | 이름 | 메서드 | 경로 | TR_ID | 필수 파라미터 |
|---|---|---|---|---|---|
| `avg_unit` | 장내채권 평균단가조회 | `GET` | `/uapi/domestic-bond/v1/quotations/avg-unit` | `CTPF2005R` | `inqr_end_dt`<br>`inqr_strt_dt`<br>`pdno`<br>`prdt_type_cd`<br>`vrfc_kind_cd` |
| `buy` | 장내채권 매수주문 | `POST` | `/uapi/domestic-bond/v1/trading/buy` | `TTTC0952U` | `bond_ord_unpr`<br>`bond_rtl_mket_yn`<br>`ord_qty2`<br>`pdno`<br>`samt_mket_ptci_yn` |
| `inquire_asking_price` | 장내채권현재가(호가) | `GET` | `/uapi/domestic-bond/v1/quotations/inquire-asking-price` | `FHKBJ773401C0` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_balance` | 장내채권 잔고조회 | `GET` | `/uapi/domestic-bond/v1/trading/inquire-balance` | `CTSC8407R` | `buy_dt`<br>`inqr_cndt`<br>`pdno` |
| `inquire_ccnl` | 장내채권현재가(체결) | `GET` | `/uapi/domestic-bond/v1/quotations/inquire-ccnl` | `FHKBJ773403C0` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_daily_ccld` | 장내채권 주문체결내역 | `GET` | `/uapi/domestic-bond/v1/trading/inquire-daily-ccld` | `CTSC8013R` | `ctx_area_fk200`<br>`ctx_area_nk200`<br>`inqr_end_dt`<br>`inqr_strt_dt`<br>`nccs_yn`<br>`pdno`<br>`sll_buy_dvsn_cd`<br>`sort_sqn_dvsn` |
| `inquire_daily_price` | 장내채권현재가(일별) | `GET` | `/uapi/domestic-bond/v1/quotations/inquire-daily-price` | `FHKBJ773404C0` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_price` | 장내채권현재가(시세) | `GET` | `/uapi/domestic-bond/v1/quotations/inquire-price` | `FHKBJ773400C0` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_psbl_order` | 장내채권 매수가능조회 | `GET` | `/uapi/domestic-bond/v1/trading/inquire-psbl-order` | `TTTC8910R` | `bond_ord_unpr`<br>`pdno` |
| `inquire_psbl_rvsecncl` | 채권정정취소가능주문조회 | `GET` | `/uapi/domestic-bond/v1/trading/inquire-psbl-rvsecncl` | `CTSC8035R` | `ctx_area_fk200`<br>`ctx_area_nk200`<br>`odno`<br>`ord_dt` |
| `issue_info` | 장내채권 발행정보 | `GET` | `/uapi/domestic-bond/v1/quotations/issue-info` | `CTPF1101R` | `pdno`<br>`prdt_type_cd` |
| `order_rvsecncl` | 장내채권 정정취소주문 | `POST` | `/uapi/domestic-bond/v1/trading/order-rvsecncl` | `TTTC0953U` | `bond_ord_unpr`<br>`ord_qty2`<br>`orgn_odno`<br>`pdno`<br>`qty_all_ord_yn`<br>`rvse_cncl_dvsn_cd` |
| `search_bond_info` | 장내채권 기본조회 | `GET` | `/uapi/domestic-bond/v1/quotations/search-bond-info` | `CTPF1114R` | `pdno`<br>`prdt_type_cd` |
| `sell` | 장내채권 매도주문 | `POST` | `/uapi/domestic-bond/v1/trading/sell` | `TTTC0958U` | `bond_ord_unpr`<br>`bond_rtl_mket_yn`<br>`ord_dvsn`<br>`ord_qty2`<br>`pdno`<br>`samt_mket_ptci_yn`<br>`sll_agco_opps_sll_yn`<br>`sprx_yn` |

### 국내선물옵션 (`domestic_futureoption`)

| API ID | 이름 | 메서드 | 경로 | TR_ID | 필수 파라미터 |
|---|---|---|---|---|---|
| `display_board_top` | 국내선물 기초자산 시세 | `GET` | `/uapi/domestic-futureoption/v1/quotations/display-board-top` | `FHPIF05030000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `exp_price_trend` | 선물옵션 일중예상체결추이 | `GET` | `/uapi/domestic-futureoption/v1/quotations/exp-price-trend` | `FHPIF05110100` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_asking_price` | 선물옵션 시세호가 | `GET` | `/uapi/domestic-futureoption/v1/quotations/inquire-asking-price` | `FHMIF10010000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_balance` | 선물옵션 잔고현황 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-balance` | `CTFO6118R`<br>`VTFO6118R` | `excc_stat_cd`<br>`mgna_dvsn` |
| `inquire_balance_settlement_pl` | 선물옵션 잔고정산손익내역 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-balance-settlement-pl` | `CTFO6117R` | `inqr_dt` |
| `inquire_balance_valuation_pl` | 선물옵션 잔고평가손익내역 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-balance-valuation-pl` | `CTFO6159R` | `excc_stat_cd`<br>`mgna_dvsn` |
| `inquire_ccnl` | 선물옵션 주문체결내역조회 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-ccnl` | `TTTO5201R`<br>`VTTO5201R` | `ccld_nccs_dvsn`<br>`end_ord_dt`<br>`sll_buy_dvsn_cd`<br>`sort_sqn`<br>`strt_ord_dt` |
| `inquire_ccnl_bstime` | 선물옵션 기준일체결내역 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-ccnl-bstime` | `CTFO5139R` | `fuop_tr_end_tmd`<br>`fuop_tr_strt_tmd`<br>`ord_dt` |
| `inquire_daily_amount_fee` | 선물옵션기간약정수수료일별 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-daily-amount-fee` | `CTFO6119R` | `inqr_end_day`<br>`inqr_strt_day` |
| `inquire_daily_fuopchartprice` | 선물옵션기간별시세(일/주/월/년) | `GET` | `/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice` | `FHKIF03020100` | `fid_cond_mrkt_div_code`<br>`fid_input_date_1`<br>`fid_input_date_2`<br>`fid_input_iscd`<br>`fid_period_div_code` |
| `inquire_deposit` | 선물옵션 총자산현황 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-deposit` | `CTRP6550R` | - |
| `inquire_ngt_balance` | (야간)선물옵션 잔고현황 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-ngt-balance` | `CTFN6118R` | `excc_stat_cd`<br>`mgna_dvsn` |
| `inquire_ngt_ccnl` | (야간)선물옵션 주문체결 내역조회 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-ngt-ccnl` | `STTN5201R` | `ccld_nccs_dvsn`<br>`end_ord_dt`<br>`sll_buy_dvsn_cd`<br>`strt_ord_dt` |
| `inquire_price` | 선물옵션 시세 | `GET` | `/uapi/domestic-futureoption/v1/quotations/inquire-price` | `FHMIF10000000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_psbl_ngt_order` | (야간)선물옵션 주문가능 조회 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-psbl-ngt-order` | `STTN5105R` | `ord_dvsn_cd`<br>`pdno`<br>`prdt_type_cd`<br>`sll_buy_dvsn_cd`<br>`unit_price` |
| `inquire_psbl_order` | 선물옵션 주문가능 | `GET` | `/uapi/domestic-futureoption/v1/trading/inquire-psbl-order` | `TTTO5105R`<br>`VTTO5105R` | `ord_dvsn_cd`<br>`pdno`<br>`sll_buy_dvsn_cd`<br>`unit_price` |
| `inquire_time_fuopchartprice` | 선물옵션 분봉조회 | `GET` | `/uapi/domestic-futureoption/v1/quotations/inquire-time-fuopchartprice` | `FHKIF03020200` | `fid_cond_mrkt_div_code`<br>`fid_fake_tick_incu_yn`<br>`fid_hour_cls_code`<br>`fid_input_date_1`<br>`fid_input_hour_1`<br>`fid_input_iscd`<br>`fid_pw_data_incu_yn` |
| `ngt_margin_detail` | (야간)선물옵션 증거금 상세 | `GET` | `/uapi/domestic-futureoption/v1/trading/ngt-margin-detail` | `CTFN7107R` | `mgna_dvsn_cd` |
| `order` | 선물옵션 주문 | `POST` | `/uapi/domestic-futureoption/v1/trading/order` | `TTTO1101U`<br>`STTN1101U`<br>`VTTO1101U` | `krx_nmpr_cndt_cd`<br>`nmpr_type_cd`<br>`ord_dv`<br>`ord_dvsn_cd`<br>`ord_prcs_dvsn_cd`<br>`ord_qty`<br>`shtn_pdno`<br>`sll_buy_dvsn_cd`<br>`unit_price` |
| `order_rvsecncl` | 선물옵션 정정취소주문 | `POST` | `/uapi/domestic-futureoption/v1/trading/order-rvsecncl` | `TTTO1103U`<br>`TTTN1103U`<br>`VTTO1103U` | `day_dv`<br>`krx_nmpr_cndt_cd`<br>`nmpr_type_cd`<br>`ord_dvsn_cd`<br>`ord_prcs_dvsn_cd`<br>`ord_qty`<br>`orgn_odno`<br>`rmn_qty_yn`<br>`rvse_cncl_dvsn_cd`<br>`unit_price` |

### 국내주식 (`domestic_stock`)

| API ID | 이름 | 메서드 | 경로 | TR_ID | 필수 파라미터 |
|---|---|---|---|---|---|
| `chk_holiday` | 국내휴장일조회 | `GET` | `/uapi/domestic-stock/v1/quotations/chk-holiday` | `CTCA0903R` | `bass_dt` |
| `comp_program_trade_daily` | 프로그램매매 종합현황(일별) | `GET` | `/uapi/domestic-stock/v1/quotations/comp-program-trade-daily` | `FHPPG04600001` | `fid_cond_mrkt_div_code`<br>`fid_mrkt_cls_code` |
| `daily_loan_trans` | 종목별 일별 대차거래추이 | `GET` | `/uapi/domestic-stock/v1/quotations/daily-loan-trans` | `HHPST074500C0` | `mksc_shrn_iscd`<br>`mrkt_div_cls_code` |
| `daily_short_sale` | 국내주식 공매도 일별추이 | `GET` | `/uapi/domestic-stock/v1/quotations/daily-short-sale` | `FHPST04830000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `estimate_perform` | 국내주식 종목추정실적 | `GET` | `/uapi/domestic-stock/v1/quotations/estimate-perform` | `HHKST668300C0` | `sht_cd` |
| `fluctuation` | 국내주식 등락률 순위 | `GET` | `/uapi/domestic-stock/v1/ranking/fluctuation` | `FHPST01700000` | `fid_cond_mrkt_div_code`<br>`fid_cond_scr_div_code`<br>`fid_div_cls_code`<br>`fid_input_cnt_1`<br>`fid_input_iscd`<br>`fid_input_price_1`<br>`fid_input_price_2`<br>`fid_prc_cls_code`<br>`fid_rank_sort_cls_code`<br>`fid_rsfl_rate1`<br>`fid_rsfl_rate2`<br>`fid_trgt_cls_code`<br>`fid_trgt_exls_cls_code`<br>`fid_vol_cnt` |
| `foreign_institution_total` | 국내기관_외국인 매매종목가집계 | `GET` | `/uapi/domestic-stock/v1/quotations/foreign-institution-total` | `FHPTJ04400000` | `fid_cond_mrkt_div_code`<br>`fid_cond_scr_div_code`<br>`fid_div_cls_code`<br>`fid_etc_cls_code`<br>`fid_input_iscd`<br>`fid_rank_sort_cls_code` |
| `frgnmem_pchs_trend` | 종목별 외국계 순매수추이 | `GET` | `/uapi/domestic-stock/v1/quotations/frgnmem-pchs-trend` | `FHKST644400C0` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd`<br>`fid_input_iscd_2` |
| `frgnmem_trade_trend` | 회원사 실시간 매매동향(틱) | `GET` | `/uapi/domestic-stock/v1/quotations/frgnmem-trade-trend` | `FHPST04320000` | `fid_cond_mrkt_div_code`<br>`fid_cond_scr_div_code`<br>`fid_input_iscd`<br>`fid_input_iscd_2`<br>`fid_mrkt_cls_code`<br>`fid_vol_cnt` |
| `inquire_account_balance` | 투자계좌자산현황조회 | `GET` | `/uapi/domestic-stock/v1/trading/inquire-account-balance` | `CTRP6548R` | - |
| `inquire_asking_price_exp_ccn` | 주식현재가 호가/예상체결 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn` | `FHKST01010200` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_balance` | 주식잔고조회 | `GET` | `/uapi/domestic-stock/v1/trading/inquire-balance` | `TTTC8434R`<br>`VTTC8434R` | `afhr_flpr_yn`<br>`fncg_amt_auto_rdpt_yn`<br>`fund_sttl_icld_yn`<br>`inqr_dvsn`<br>`prcs_dvsn`<br>`unpr_dvsn` |
| `inquire_balance_rlz_pl` | 주식잔고조회_실현손익 | `GET` | `/uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl` | `TTTC8494R` | `afhr_flpr_yn`<br>`fncg_amt_auto_rdpt_yn`<br>`fund_sttl_icld_yn`<br>`inqr_dvsn`<br>`prcs_dvsn`<br>`unpr_dvsn` |
| `inquire_ccnl` | 주식현재가 체결 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-ccnl` | `FHKST01010300` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_credit_psamount` | 신용매수가능조회 | `GET` | `/uapi/domestic-stock/v1/trading/inquire-credit-psamount` | `TTTC8909R` | `cma_evlu_amt_icld_yn`<br>`crdt_type`<br>`ord_dvsn`<br>`ovrs_icld_yn`<br>`pdno` |
| `inquire_daily_ccld` | 주식일별주문체결조회 | `GET` | `/uapi/domestic-stock/v1/trading/inquire-daily-ccld` | `CTSC9215R`<br>`TTTC0081R`<br>`VTSC9215R`<br>`VTTC0081R` | `ccld_dvsn`<br>`inqr_dvsn`<br>`inqr_dvsn_3`<br>`inqr_end_dt`<br>`inqr_strt_dt`<br>`pd_dv`<br>`sll_buy_dvsn_cd` |
| `inquire_daily_indexchartprice` | 국내주식업종기간별시세(일/주/월/년) | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice` | `FHKUP03500100` | `fid_cond_mrkt_div_code`<br>`fid_input_date_1`<br>`fid_input_date_2`<br>`fid_input_iscd`<br>`fid_period_div_code` |
| `inquire_daily_itemchartprice` | 국내주식기간별시세(일/주/월/년) | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice` | `FHKST03010100` | `fid_cond_mrkt_div_code`<br>`fid_input_date_1`<br>`fid_input_date_2`<br>`fid_input_iscd`<br>`fid_org_adj_prc`<br>`fid_period_div_code` |
| `inquire_daily_overtimeprice` | 주식현재가 시간외일자별주가 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-daily-overtimeprice` | `FHPST02320000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_daily_price` | 주식현재가 일자별 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-daily-price` | `FHKST01010400` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd`<br>`fid_org_adj_prc`<br>`fid_period_div_code` |
| `inquire_daily_trade_volume` | 종목별일별매수매도체결량 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-daily-trade-volume` | `FHKST03010800` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd`<br>`fid_period_div_code` |
| `inquire_elw_price` | ELW 현재가 시세 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-elw-price` | `FHKEW15010000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_index_daily_price` | 국내업종 일자별지수 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-index-daily-price` | `FHPUP02120000` | `fid_cond_mrkt_div_code`<br>`fid_input_date_1`<br>`fid_input_iscd`<br>`fid_period_div_code` |
| `inquire_index_price` | 국내업종 현재지수 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-index-price` | `FHPUP02100000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_investor` | 주식현재가 투자자 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-investor` | `FHKST01010900` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_investor_daily_by_market` | 시장별 투자자매매동향(일별) | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-investor-daily-by-market` | `FHPTJ04040000` | `fid_cond_mrkt_div_code`<br>`fid_input_date_1`<br>`fid_input_date_2`<br>`fid_input_iscd`<br>`fid_input_iscd_1`<br>`fid_input_iscd_2` |
| `inquire_investor_time_by_market` | 시장별 투자자매매동향(시세) | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-investor-time-by-market` | `FHPTJ04030000` | `fid_input_iscd`<br>`fid_input_iscd_2` |
| `inquire_member` | 주식현재가 회원사 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-member` | `FHKST01010600` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_member_daily` | 주식현재가 회원사 종목매매동향 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-member-daily` | `FHPST04540000` | `fid_cond_mrkt_div_code`<br>`fid_input_date_1`<br>`fid_input_date_2`<br>`fid_input_iscd`<br>`fid_input_iscd_2` |
| `inquire_overtime_asking_price` | 국내주식 시간외호가 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-overtime-asking-price` | `FHPST02300400` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_overtime_price` | 국내주식 시간외현재가 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-overtime-price` | `FHPST02300000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_period_profit` | 기간별손익일별합산조회 | `GET` | `/uapi/domestic-stock/v1/trading/inquire-period-profit` | `TTTC8708R` | `cblc_dvsn`<br>`inqr_dvsn`<br>`inqr_end_dt`<br>`inqr_strt_dt`<br>`sort_dvsn` |
| `inquire_period_trade_profit` | 기간별매매손익현황조회 | `GET` | `/uapi/domestic-stock/v1/trading/inquire-period-trade-profit` | `TTTC8715R` | `cblc_dvsn`<br>`inqr_end_dt`<br>`inqr_strt_dt`<br>`sort_dvsn` |
| `inquire_price` | 주식현재가 시세 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-price` | `FHKST01010100` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_price_2` | 주식현재가 시세2 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-price-2` | `FHPST01010000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `inquire_psbl_order` | 매수가능조회 | `GET` | `/uapi/domestic-stock/v1/trading/inquire-psbl-order` | `TTTC8908R`<br>`VTTC8908R` | `cma_evlu_amt_icld_yn`<br>`ord_dvsn`<br>`ord_unpr`<br>`ovrs_icld_yn`<br>`pdno` |
| `inquire_psbl_rvsecncl` | 주식정정취소가능주문조회 | `GET` | `/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl` | `TTTC0084R` | `inqr_dvsn_1`<br>`inqr_dvsn_2` |
| `inquire_psbl_sell` | 매도가능수량조회 | `GET` | `/uapi/domestic-stock/v1/trading/inquire-psbl-sell` | `TTTC8408R` | `pdno` |
| `inquire_time_dailychartprice` | 주식일별분봉조회 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice` | `FHKST03010230` | `fid_cond_mrkt_div_code`<br>`fid_input_date_1`<br>`fid_input_hour_1`<br>`fid_input_iscd` |
| `inquire_time_indexchartprice` | 업종 분봉조회 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-time-indexchartprice` | `FHKUP03500200` | `fid_cond_mrkt_div_code`<br>`fid_etc_cls_code`<br>`fid_input_hour_1`<br>`fid_input_iscd`<br>`fid_pw_data_incu_yn` |
| `inquire_time_itemchartprice` | 주식당일분봉조회 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice` | `FHKST03010200` | `fid_cond_mrkt_div_code`<br>`fid_input_hour_1`<br>`fid_input_iscd`<br>`fid_pw_data_incu_yn` |
| `inquire_time_itemconclusion` | 주식현재가 당일시간대별체결 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion` | `FHPST01060000` | `fid_cond_mrkt_div_code`<br>`fid_input_hour_1`<br>`fid_input_iscd` |
| `inquire_time_overtimeconclusion` | 주식현재가 시간외시간별체결 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-time-overtimeconclusion` | `FHPST02310000` | `fid_cond_mrkt_div_code`<br>`fid_hour_cls_code`<br>`fid_input_iscd` |
| `inquire_vi_status` | 변동성완화장치(VI) 현황 | `GET` | `/uapi/domestic-stock/v1/quotations/inquire-vi-status` | `FHPST01390000` | `fid_cond_scr_div_code`<br>`fid_div_cls_code`<br>`fid_input_date_1`<br>`fid_input_iscd`<br>`fid_mrkt_cls_code`<br>`fid_rank_sort_cls_code`<br>`fid_trgt_cls_code`<br>`fid_trgt_exls_cls_code` |
| `intgr_margin` | 주식통합증거금 현황 | `GET` | `/uapi/domestic-stock/v1/trading/intgr-margin` | `TTTC0869R` | `cma_evlu_amt_icld_yn`<br>`fwex_ctrt_frcr_dvsn_cd`<br>`wcrc_frcr_dvsn_cd` |
| `intstock_multprice` | 관심종목(멀티종목) 시세조회 | `GET` | `/uapi/domestic-stock/v1/quotations/intstock-multprice` | `FHKST11300006` | `fid_cond_mrkt_div_code_1`<br>`fid_input_iscd_1` |
| `intstock_stocklist_by_group` | 관심종목 그룹별 종목조회 | `GET` | `/uapi/domestic-stock/v1/quotations/intstock-stocklist-by-group` | `HHKCM113004C6` | `fid_etc_cls_code`<br>`inter_grp_code`<br>`type`<br>`user_id` |
| `invest_opbysec` | 국내주식 증권사별 투자의견 | `GET` | `/uapi/domestic-stock/v1/quotations/invest-opbysec` | `FHKST663400C0` | `fid_cond_mrkt_div_code`<br>`fid_cond_scr_div_code`<br>`fid_div_cls_code`<br>`fid_input_date_1`<br>`fid_input_date_2`<br>`fid_input_iscd` |
| `invest_opinion` | 국내주식 종목투자의견 | `GET` | `/uapi/domestic-stock/v1/quotations/invest-opinion` | `FHKST663300C0` | `fid_cond_mrkt_div_code`<br>`fid_cond_scr_div_code`<br>`fid_input_date_1`<br>`fid_input_date_2`<br>`fid_input_iscd` |
| `investor_program_trade_today` | 프로그램매매 투자자매매동향(당일) | `GET` | `/uapi/domestic-stock/v1/quotations/investor-program-trade-today` | `HHPPG046600C1` | `mrkt_div_cls_code` |
| `investor_trade_by_stock_daily` | 종목별 투자자매매동향(일별) | `GET` | `/uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily` | `FHPTJ04160001` | `fid_cond_mrkt_div_code`<br>`fid_input_date_1`<br>`fid_input_iscd` |
| `investor_trend_estimate` | 종목별 외인기관 추정가집계 | `GET` | `/uapi/domestic-stock/v1/quotations/investor-trend-estimate` | `HHPTJ04160200` | `mksc_shrn_iscd` |
| `market_cap` | 국내주식 시가총액 상위 | `GET` | `/uapi/domestic-stock/v1/ranking/market-cap` | `FHPST01740000` | `fid_cond_mrkt_div_code`<br>`fid_cond_scr_div_code`<br>`fid_div_cls_code`<br>`fid_input_iscd`<br>`fid_input_price_1`<br>`fid_input_price_2`<br>`fid_trgt_cls_code`<br>`fid_trgt_exls_cls_code`<br>`fid_vol_cnt` |
| `news_title` | 종합 시황/공시(제목) | `GET` | `/uapi/domestic-stock/v1/quotations/news-title` | `FHKST01011800` | `fid_cond_mrkt_cls_code`<br>`fid_input_date_1`<br>`fid_input_hour_1`<br>`fid_input_iscd`<br>`fid_input_srno`<br>`fid_news_ofer_entp_code`<br>`fid_rank_sort_cls_code`<br>`fid_titl_cntt` |
| `order_cash` | 주식주문(현금) | `POST` | `/uapi/domestic-stock/v1/trading/order-cash` | `TTTC0011U`<br>`TTTC0012U`<br>`VTTC0011U`<br>`VTTC0012U` | `excg_id_dvsn_cd`<br>`ord_dv`<br>`ord_dvsn`<br>`ord_qty`<br>`ord_unpr`<br>`pdno` |
| `order_credit` | 주식주문(신용) | `POST` | `/uapi/domestic-stock/v1/trading/order-credit` | `TTTC0052U`<br>`TTTC0051U` | `crdt_type`<br>`loan_dt`<br>`ord_dv`<br>`ord_dvsn`<br>`ord_qty`<br>`ord_unpr`<br>`pdno` |
| `order_resv` | 주식예약주문 | `POST` | `/uapi/domestic-stock/v1/trading/order-resv` | `CTSC0008U` | `ord_dvsn_cd`<br>`ord_objt_cblc_dvsn_cd`<br>`ord_qty`<br>`ord_unpr`<br>`pdno`<br>`sll_buy_dvsn_cd` |
| `order_resv_ccnl` | 주식예약주문조회 | `GET` | `/uapi/domestic-stock/v1/trading/order-resv-ccnl` | `CTSC0004R` | `cncl_yn`<br>`prcs_dvsn_cd`<br>`rsvn_ord_end_dt`<br>`rsvn_ord_ord_dt`<br>`tmnl_mdia_kind_cd` |
| `order_resv_rvsecncl` | 주식예약주문정정취소 | `POST` | `/uapi/domestic-stock/v1/trading/order-resv-rvsecncl` | `CTSC0009U`<br>`CTSC0013U` | `ord_type`<br>`rsvn_ord_ord_dt`<br>`rsvn_ord_orgno`<br>`rsvn_ord_seq` |
| `order_rvsecncl` | 주식주문(정정취소) | `POST` | `/uapi/domestic-stock/v1/trading/order-rvsecncl` | `TTTC0013U`<br>`VTTC0013U` | `excg_id_dvsn_cd`<br>`krx_fwdg_ord_orgno`<br>`ord_dvsn`<br>`ord_qty`<br>`ord_unpr`<br>`orgn_odno`<br>`qty_all_ord_yn`<br>`rvse_cncl_dvsn_cd` |
| `pension_inquire_balance` | 퇴직연금 잔고조회 | `GET` | `/uapi/domestic-stock/v1/trading/pension/inquire-balance` | `TTTC2208R` | `acca_dvsn_cd`<br>`inqr_dvsn` |
| `pension_inquire_daily_ccld` | 퇴직연금 미체결내역 | `GET` | `/uapi/domestic-stock/v1/trading/pension/inquire-daily-ccld` | `TTTC2201R` | `ccld_nccs_dvsn`<br>`inqr_dvsn_3`<br>`sll_buy_dvsn_cd`<br>`user_dvsn_cd` |
| `pension_inquire_deposit` | 퇴직연금 예수금조회 | `GET` | `/uapi/domestic-stock/v1/trading/pension/inquire-deposit` | `TTTC0506R` | `acca_dvsn_cd` |
| `pension_inquire_present_balance` | 퇴직연금 체결기준잔고 | `GET` | `/uapi/domestic-stock/v1/trading/pension/inquire-present-balance` | `TTTC2202R` | `user_dvsn_cd` |
| `pension_inquire_psbl_order` | 퇴직연금 매수가능조회 | `GET` | `/uapi/domestic-stock/v1/trading/pension/inquire-psbl-order` | `TTTC0503R` | `acca_dvsn_cd`<br>`cma_evlu_amt_icld_yn`<br>`ord_dvsn`<br>`ord_unpr`<br>`pdno` |
| `period_rights` | 기간별계좌권리현황조회 | `GET` | `/uapi/domestic-stock/v1/trading/period-rights` | `CTRGA011R` | `inqr_dvsn`<br>`inqr_end_dt`<br>`inqr_strt_dt` |
| `program_trade_by_stock` | 종목별 프로그램매매추이(체결) | `GET` | `/uapi/domestic-stock/v1/quotations/program-trade-by-stock` | `FHPPG04650101` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `program_trade_by_stock_daily` | 종목별 프로그램매매추이(일별) | `GET` | `/uapi/domestic-stock/v1/quotations/program-trade-by-stock-daily` | `FHPPG04650201` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `psearch_result` | 종목조건검색조회 | `GET` | `/uapi/domestic-stock/v1/quotations/psearch-result` | `HHKST03900400` | `user_id` |
| `psearch_title` | 종목조건검색 목록조회 | `GET` | `/uapi/domestic-stock/v1/quotations/psearch-title` | `HHKST03900300` | `user_id` |
| `search_info` | 상품기본조회 | `GET` | `/uapi/domestic-stock/v1/quotations/search-info` | `CTPF1604R` | `pdno`<br>`prdt_type_cd` |
| `search_stock_info` | 주식기본조회 | `GET` | `/uapi/domestic-stock/v1/quotations/search-stock-info` | `CTPF1002R` | `pdno`<br>`prdt_type_cd` |
| `volume_power` | 국내주식 체결강도 상위 | `GET` | `/uapi/domestic-stock/v1/ranking/volume-power` | `FHPST01680000` | `fid_cond_mrkt_div_code`<br>`fid_cond_scr_div_code`<br>`fid_div_cls_code`<br>`fid_input_iscd`<br>`fid_input_price_1`<br>`fid_input_price_2`<br>`fid_trgt_cls_code`<br>`fid_trgt_exls_cls_code`<br>`fid_vol_cnt` |
| `volume_rank` | 거래량순위 | `GET` | `/uapi/domestic-stock/v1/quotations/volume-rank` | `FHPST01710000` | `fid_blng_cls_code`<br>`fid_cond_mrkt_div_code`<br>`fid_cond_scr_div_code`<br>`fid_div_cls_code`<br>`fid_input_date_1`<br>`fid_input_iscd`<br>`fid_input_price_1`<br>`fid_input_price_2`<br>`fid_trgt_cls_code`<br>`fid_trgt_exls_cls_code`<br>`fid_vol_cnt` |

### ELW (`elw`)

| API ID | 이름 | 메서드 | 경로 | TR_ID | 필수 파라미터 |
|---|---|---|---|---|---|
| `volume_rank` | ELW 거래량순위 | `GET` | `/uapi/elw/v1/ranking/volume-rank` | `FHPEW02780000` | `fid_blng_cls_code`<br>`fid_cond_mrkt_div_code`<br>`fid_cond_scr_div_code`<br>`fid_div_cls_code`<br>`fid_input_date_1`<br>`fid_input_date_2`<br>`fid_input_iscd`<br>`fid_input_iscd_2`<br>`fid_input_price_1`<br>`fid_input_price_2`<br>`fid_input_rmnn_dynu_1`<br>`fid_input_vol_1`<br>`fid_input_vol_2`<br>`fid_rank_sort_cls_code`<br>`fid_unas_input_iscd` |

### ETF/ETN (`etfetn`)

| API ID | 이름 | 메서드 | 경로 | TR_ID | 필수 파라미터 |
|---|---|---|---|---|---|
| `inquire_price` | ETF/ETN 현재가 | `GET` | `/uapi/etfetn/v1/quotations/inquire-price` | `FHPST02400000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |
| `nav_comparison_trend` | NAV 비교추이(종목) | `GET` | `/uapi/etfetn/v1/quotations/nav-comparison-trend` | `FHPST02440000` | `fid_cond_mrkt_div_code`<br>`fid_input_iscd` |

### 해외선물옵션 (`overseas_futureoption`)

| API ID | 이름 | 메서드 | 경로 | TR_ID | 필수 파라미터 |
|---|---|---|---|---|---|
| `daily_ccnl` | 해외선물 체결추이(일간) | `GET` | `/uapi/overseas-futureoption/v1/quotations/daily-ccnl` | `HHDFC55020100` | `close_date_time`<br>`exch_cd`<br>`index_key`<br>`qry_cnt`<br>`qry_gap`<br>`qry_tp`<br>`srs_cd`<br>`start_date_time` |
| `inquire_asking_price` | 해외선물 호가 | `GET` | `/uapi/overseas-futureoption/v1/quotations/inquire-asking-price` | `HHDFC86000000` | `srs_cd` |
| `inquire_ccld` | 해외선물옵션 당일주문내역조회 | `GET` | `/uapi/overseas-futureoption/v1/trading/inquire-ccld` | `OTFM3116R` | `ccld_nccs_dvsn`<br>`ctx_area_fk200`<br>`ctx_area_nk200`<br>`fuop_dvsn`<br>`sll_buy_dvsn_cd` |
| `inquire_daily_ccld` | 해외선물옵션 일별 체결내역 | `GET` | `/uapi/overseas-futureoption/v1/trading/inquire-daily-ccld` | `OTFM3122R` | `crcy_cd`<br>`ctx_area_fk200`<br>`ctx_area_nk200`<br>`end_dt`<br>`fm_item_ftng_yn`<br>`fuop_dvsn_cd`<br>`sll_buy_dvsn_cd`<br>`strt_dt` |
| `inquire_daily_order` | 해외선물옵션 일별 주문내역 | `GET` | `/uapi/overseas-futureoption/v1/trading/inquire-daily-order` | `OTFM3120R` | `ccld_nccs_dvsn`<br>`ctx_area_fk200`<br>`ctx_area_nk200`<br>`end_dt`<br>`fm_pdgr_cd`<br>`fuop_dvsn`<br>`sll_buy_dvsn_cd`<br>`strt_dt` |
| `inquire_deposit` | 해외선물옵션 예수금현황 | `GET` | `/uapi/overseas-futureoption/v1/trading/inquire-deposit` | `OTFM1411R` | `crcy_cd`<br>`inqr_dt` |
| `inquire_period_ccld` | 해외선물옵션 기간계좌손익 일별 | `GET` | `/uapi/overseas-futureoption/v1/trading/inquire-period-ccld` | `OTFM3118R` | `crcy_cd`<br>`ctx_area_fk200`<br>`ctx_area_nk200`<br>`fuop_dvsn`<br>`inqr_term_from_dt`<br>`inqr_term_to_dt`<br>`whol_trsl_yn` |
| `inquire_period_trans` | 해외선물옵션 기간계좌거래내역 | `GET` | `/uapi/overseas-futureoption/v1/trading/inquire-period-trans` | `OTFM3114R` | `acnt_tr_type_cd`<br>`crcy_cd`<br>`ctx_area_fk100`<br>`ctx_area_nk100`<br>`inqr_term_from_dt`<br>`inqr_term_to_dt`<br>`pwd_chk_yn` |
| `inquire_price` | 해외선물종목현재가 | `GET` | `/uapi/overseas-futureoption/v1/quotations/inquire-price` | `HHDFC55010000` | `srs_cd` |
| `inquire_psamount` | 해외선물옵션 주문가능조회 | `GET` | `/uapi/overseas-futureoption/v1/trading/inquire-psamount` | `OTFM3304R` | `ecis_rsvn_ord_yn`<br>`fm_ord_pric`<br>`ovrs_futr_fx_pdno`<br>`sll_buy_dvsn_cd` |
| `inquire_time_futurechartprice` | 해외선물 분봉조회 | `GET` | `/uapi/overseas-futureoption/v1/quotations/inquire-time-futurechartprice` | `HHDFC55020400` | `close_date_time`<br>`exch_cd`<br>`index_key`<br>`qry_cnt`<br>`qry_gap`<br>`qry_tp`<br>`srs_cd`<br>`start_date_time` |
| `inquire_unpd` | 해외선물옵션 미결제내역조회(잔고) | `GET` | `/uapi/overseas-futureoption/v1/trading/inquire-unpd` | `OTFM1412R` | `ctx_area_fk100`<br>`ctx_area_nk100`<br>`fuop_dvsn` |
| `margin_detail` | 해외선물옵션 증거금상세 | `GET` | `/uapi/overseas-futureoption/v1/trading/margin-detail` | `OTFM3115R` | `crcy_cd`<br>`inqr_dt` |
| `opt_asking_price` | 해외옵션 호가 | `GET` | `/uapi/overseas-futureoption/v1/quotations/opt-asking-price` | `HHDFO86000000` | `srs_cd` |
| `opt_price` | 해외옵션종목현재가 | `GET` | `/uapi/overseas-futureoption/v1/quotations/opt-price` | `HHDFO55010000` | `srs_cd` |
| `order` | 해외선물옵션 주문 | `POST` | `/uapi/overseas-futureoption/v1/trading/order` | `OTFM3001U` | `ccld_cndt_cd`<br>`cplx_ord_dvsn_cd`<br>`ecis_rsvn_ord_yn`<br>`fm_hdge_ord_scrn_yn`<br>`fm_limit_ord_pric`<br>`fm_lqd_lmt_ord_pric`<br>`fm_lqd_stop_ord_pric`<br>`fm_lqd_ustl_ccld_dt`<br>`fm_lqd_ustl_ccno`<br>`fm_ord_qty`<br>`fm_stop_ord_pric`<br>`ovrs_futr_fx_pdno`<br>`pric_dvsn_cd`<br>`sll_buy_dvsn_cd` |
| `order_rvsecncl` | 해외선물옵션 정정취소주문 | `POST` | `/uapi/overseas-futureoption/v1/trading/order-rvsecncl` | `OTFM3002U`<br>`OTFM3003U` | `fm_hdge_ord_scrn_yn`<br>`fm_limit_ord_pric`<br>`fm_lqd_lmt_ord_pric`<br>`fm_lqd_stop_ord_pric`<br>`fm_mkpr_cvsn_yn`<br>`fm_stop_ord_pric`<br>`ord_dv`<br>`orgn_odno`<br>`orgn_ord_dt` |
| `search_contract_detail` | 해외선물 상품기본정보 | `GET` | `/uapi/overseas-futureoption/v1/quotations/search-contract-detail` | `HHDFC55200000` | `qry_cnt` |
| `search_opt_detail` | 해외옵션 상품기본정보 | `GET` | `/uapi/overseas-futureoption/v1/quotations/search-opt-detail` | `HHDFO55200000` | `qry_cnt`<br>`srs_cd_01` |

### 해외주식 (`overseas_stock`)

| API ID | 이름 | 메서드 | 경로 | TR_ID | 필수 파라미터 |
|---|---|---|---|---|---|
| `algo_ordno` | 해외주식 지정가주문번호조회 | `GET` | `/uapi/overseas-stock/v1/trading/algo-ordno` | `TTTS6058R` | `trad_dt` |
| `dailyprice` | 해외주식 기간별시세 | `GET` | `/uapi/overseas-price/v1/quotations/dailyprice` | `HHDFS76240000` | `auth`<br>`bymd`<br>`excd`<br>`gubn`<br>`modp`<br>`symb` |
| `daytime_order` | 해외주식 미국주간주문 | `POST` | `/uapi/overseas-stock/v1/trading/daytime-order` | `TTTS6036U`<br>`TTTS6037U` | `ctac_tlno`<br>`mgco_aptm_odno`<br>`ord_dvsn`<br>`ord_qty`<br>`ord_svr_dvsn_cd`<br>`order_dv`<br>`ovrs_excg_cd`<br>`ovrs_ord_unpr`<br>`pdno` |
| `daytime_order_rvsecncl` | 해외주식 미국주간정정취소 | `POST` | `/uapi/overseas-stock/v1/trading/daytime-order-rvsecncl` | `TTTS6038U` | `ctac_tlno`<br>`mgco_aptm_odno`<br>`ord_qty`<br>`ord_svr_dvsn_cd`<br>`orgn_odno`<br>`ovrs_excg_cd`<br>`ovrs_ord_unpr`<br>`pdno`<br>`rvse_cncl_dvsn_cd` |
| `foreign_margin` | 해외증거금 통화별조회 | `GET` | `/uapi/overseas-stock/v1/trading/foreign-margin` | `TTTC2101R` | - |
| `industry_theme` | 해외주식 업종별시세 | `GET` | `/uapi/overseas-price/v1/quotations/industry-theme` | `HHDFS76370000` | `excd`<br>`icod`<br>`vol_rang` |
| `inquire_algo_ccnl` | 해외주식 지정가체결내역조회 | `GET` | `/uapi/overseas-stock/v1/trading/inquire-algo-ccnl` | `TTTS6059R` | - |
| `inquire_asking_price` | 해외주식 현재가 1호가 | `GET` | `/uapi/overseas-price/v1/quotations/inquire-asking-price` | `HHDFS76200100` | `auth`<br>`excd`<br>`symb` |
| `inquire_balance` | 해외주식 잔고 | `GET` | `/uapi/overseas-stock/v1/trading/inquire-balance` | `TTTS3012R`<br>`VTTS3012R` | `ovrs_excg_cd`<br>`tr_crcy_cd` |
| `inquire_ccnl` | 해외주식 주문체결내역 | `GET` | `/uapi/overseas-stock/v1/trading/inquire-ccnl` | `TTTS3035R`<br>`VTTS3035R` | `ccld_nccs_dvsn`<br>`odno`<br>`ord_dt`<br>`ord_end_dt`<br>`ord_gno_brno`<br>`ord_strt_dt`<br>`pdno`<br>`sll_buy_dvsn`<br>`sort_sqn` |
| `inquire_daily_chartprice` | 해외주식 종목/지수/환율기간별시세(일/주/월/년) | `GET` | `/uapi/overseas-price/v1/quotations/inquire-daily-chartprice` | `FHKST03030100` | `fid_cond_mrkt_div_code`<br>`fid_input_date_1`<br>`fid_input_date_2`<br>`fid_input_iscd`<br>`fid_period_div_code` |
| `inquire_nccs` | 해외주식 미체결내역 | `GET` | `/uapi/overseas-stock/v1/trading/inquire-nccs` | `TTTS3018R` | `ovrs_excg_cd`<br>`sort_sqn` |
| `inquire_paymt_stdr_balance` | 해외주식 결제기준잔고 | `GET` | `/uapi/overseas-stock/v1/trading/inquire-paymt-stdr-balance` | `CTRP6010R` | `bass_dt`<br>`inqr_dvsn_cd`<br>`wcrc_frcr_dvsn_cd` |
| `inquire_period_profit` | 해외주식 기간손익 | `GET` | `/uapi/overseas-stock/v1/trading/inquire-period-profit` | `TTTS3039R` | `inqr_end_dt`<br>`inqr_strt_dt`<br>`ovrs_excg_cd`<br>`wcrc_frcr_dvsn_cd` |
| `inquire_period_trans` | 해외주식 일별거래내역 | `GET` | `/uapi/overseas-stock/v1/trading/inquire-period-trans` | `CTOS4001R` | `erlm_end_dt`<br>`erlm_strt_dt`<br>`loan_dvsn_cd`<br>`ovrs_excg_cd`<br>`pdno`<br>`sll_buy_dvsn_cd` |
| `inquire_present_balance` | 해외주식 체결기준현재잔고 | `GET` | `/uapi/overseas-stock/v1/trading/inquire-present-balance` | `CTRP6504R`<br>`VTRP6504R` | `inqr_dvsn_cd`<br>`natn_cd`<br>`tr_mket_cd`<br>`wcrc_frcr_dvsn_cd` |
| `inquire_psamount` | 해외주식 매수가능금액조회 | `GET` | `/uapi/overseas-stock/v1/trading/inquire-psamount` | `TTTS3007R`<br>`VTTS3007R` | `item_cd`<br>`ovrs_excg_cd`<br>`ovrs_ord_unpr` |
| `inquire_search` | 해외주식조건검색 | `GET` | `/uapi/overseas-price/v1/quotations/inquire-search` | `HHDFS76410000` | `auth`<br>`co_en_amt`<br>`co_en_eps`<br>`co_en_per`<br>`co_en_pricecur`<br>`co_en_rate`<br>`co_en_shar`<br>`co_en_valx`<br>`co_en_volume`<br>`co_st_amt`<br>`co_st_eps`<br>`co_st_per`<br>`co_st_pricecur`<br>`co_st_rate`<br>`co_st_shar`<br>`co_st_valx`<br>`co_st_volume`<br>`co_yn_amt`<br>`co_yn_eps`<br>`co_yn_per`<br>`co_yn_pricecur`<br>`co_yn_rate`<br>`co_yn_shar`<br>`co_yn_valx`<br>`co_yn_volume`<br>`excd`<br>`keyb` |
| `inquire_time_indexchartprice` | 해외지수분봉조회 | `GET` | `/uapi/overseas-price/v1/quotations/inquire-time-indexchartprice` | `FHKST03030200` | `fid_cond_mrkt_div_code`<br>`fid_hour_cls_code`<br>`fid_input_iscd`<br>`fid_pw_data_incu_yn` |
| `inquire_time_itemchartprice` | 해외주식분봉조회 | `GET` | `/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice` | `HHDFS76950200` | `auth`<br>`excd`<br>`fill`<br>`keyb`<br>`next`<br>`nmin`<br>`nrec`<br>`pinc`<br>`symb` |
| `order` | 해외주식 주문 | `POST` | `/uapi/overseas-stock/v1/trading/order` | `TTTT1002U`<br>`TTTS1002U`<br>`TTTT1006U`<br>`TTTS0202U`<br>`TTTS1001U`<br>`TTTS0305U`<br>`TTTS1005U`<br>`TTTS0308U`<br>`TTTS0304U`<br>`TTTS0311U`<br>`TTTS0307U`<br>`TTTS0310U` | `ctac_tlno`<br>`mgco_aptm_odno`<br>`ord_dv`<br>`ord_dvsn`<br>`ord_qty`<br>`ord_svr_dvsn_cd`<br>`ovrs_excg_cd`<br>`ovrs_ord_unpr`<br>`pdno` |
| `order_resv` | 해외주식 예약주문접수 | `POST` | `/uapi/overseas-stock/v1/trading/order-resv` | `TTTT3014U`<br>`TTTT3016U`<br>`VTTT3014U`<br>`TTTS3013U`<br>`VTTT3016U`<br>`VTTS3013U` | `ft_ord_qty`<br>`ft_ord_unpr3`<br>`ord_dv`<br>`ovrs_excg_cd`<br>`pdno` |
| `order_resv_ccnl` | 해외주식 예약주문접수취소 | `POST` | `/uapi/overseas-stock/v1/trading/order-resv-ccnl` | `TTTT3017U`<br>`VTTT3017U` | `nat_dv`<br>`ovrs_rsvn_odno`<br>`rsvn_ord_rcit_dt` |
| `order_resv_list` | 해외주식 예약주문조회 | `GET` | `/uapi/overseas-stock/v1/trading/order-resv-list` | `TTTT3039R`<br>`TTTS3014R` | `inqr_dvsn_cd`<br>`inqr_end_dt`<br>`inqr_strt_dt`<br>`nat_dv`<br>`ovrs_excg_cd` |
| `order_rvsecncl` | 해외주식 정정취소주문 | `POST` | `/uapi/overseas-stock/v1/trading/order-rvsecncl` | `TTTT1004U`<br>`VTTT1004U` | `mgco_aptm_odno`<br>`ord_qty`<br>`ord_svr_dvsn_cd`<br>`orgn_odno`<br>`ovrs_excg_cd`<br>`ovrs_ord_unpr`<br>`pdno`<br>`rvse_cncl_dvsn_cd` |
| `period_rights` | 해외주식 기간별권리조회 | `GET` | `/uapi/overseas-price/v1/quotations/period-rights` | `CTRGT011R` | `inqr_dvsn_cd`<br>`inqr_end_dt`<br>`inqr_strt_dt`<br>`rght_type_cd` |
| `price` | 해외주식 현재체결가 | `GET` | `/uapi/overseas-price/v1/quotations/price` | `HHDFS00000300` | `auth`<br>`excd`<br>`symb` |
| `price_detail` | 해외주식 현재가상세 | `GET` | `/uapi/overseas-price/v1/quotations/price-detail` | `HHDFS76200200` | `auth`<br>`excd`<br>`symb` |
| `price_fluct` | 해외주식 가격급등락 | `GET` | `/uapi/overseas-stock/v1/ranking/price-fluct` | `HHDFS76260000` | `excd`<br>`gubn`<br>`minx`<br>`vol_rang` |
| `quot_inquire_ccnl` | 해외주식 체결추이 | `GET` | `/uapi/overseas-price/v1/quotations/inquire-ccnl` | `HHDFS76200300` | `excd`<br>`symb`<br>`tday` |
| `rights_by_ice` | 해외주식 권리종합 | `GET` | `/uapi/overseas-price/v1/quotations/rights-by-ice` | `HHDFS78330900` | `ncod`<br>`symb` |
| `search_info` | 해외주식 상품기본정보 | `GET` | `/uapi/overseas-price/v1/quotations/search-info` | `CTPF1702R` | `pdno`<br>`prdt_type_cd` |
| `trade_vol` | 해외주식 거래량순위 | `GET` | `/uapi/overseas-stock/v1/ranking/trade-vol` | `HHDFS76310010` | `excd`<br>`nday`<br>`vol_rang` |
| `updown_rate` | 해외주식 상승율/하락율 | `GET` | `/uapi/overseas-stock/v1/ranking/updown-rate` | `HHDFS76290000` | `excd`<br>`gubn`<br>`nday`<br>`vol_rang` |
