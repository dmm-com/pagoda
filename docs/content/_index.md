---
title: Pagoda
---

<span class="badge-placeholder">[![Build core (Python / Django)](https://github.com/dmm-com/pagoda/actions/workflows/build-core.yml/badge.svg)](https://github.com/dmm-com/pagoda/actions/workflows/build-core.yml)</span>
<span class="badge-placeholder">[![Build frontend](https://github.com/dmm-com/pagoda/actions/workflows/build-frontend.yml/badge.svg)](https://github.com/dmm-com/pagoda/actions/workflows/build-frontend.yml)</span>
<span class="badge-placeholder">[![License: MIT](https://img.shields.io/github/license/dmm-com/airone)](https://github.com/dmm-com/pagoda/blob/master/LICENSE)</span>

Pagoda is a Web Application which is developed by the infrastructure division of DMM.com LLC on the purpose of managing information which is associated with on-premise equipments. This aims to be versatile and flexible for doing it.

In regard to the DMM.com, Pagoda is responsible for managing all phisical (e.g. where a Server is equipped on), logical (e.g. which IPv4/v6 addresses are binded to), managemental (e.g. accounting details for equipments), operational (e.g. who and how uses it) information. And this meets demands of individual departs departments that handle each different information and have own work styles.

We had managed those information by using a DCIM (a.k.a. Data Center Information Management) system and many spreadsheets which are related to it until then. Basic physical and logical information was managed in the DCIM. And other spreadsheets had related managemental and operational information. Sadly, there were many different similer spreadsheets that have same information. 

When it comes to a equipments of Server, Data Center team has an interest in what kind of transceivers (SFP?, SFP+? or QSFP?) are installed on its ports. On the other hand, Contents Provider team is interested in storage devices on it. And Accounting team cares when they and how they were purchased. Please imagine a situation that individual teams try to handle those information by own spreadsheets. It's nightmare to keep consistency of all those spreadsheets once its physical (this Server) would be disposed.

The original motivation of developing this software is solving this problem. If you are interested in more information about it, please check below page.
(https://www.janog.gr.jp/meeting/janog45/en/program/infrabcp)
