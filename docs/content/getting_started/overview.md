---
title: AirOne Overview
weight: 0
---

AirOne is an information management system with high flexibility of access control and high extensibility of data. This enables to manage information in any type of use-cases. This document describes these features.

### Data model that meets with extensibility

AirOne manages informaiton by using following two type of data-structure.

* Entity - has meta data (what kind of data it has and how).
* Entry - has actual data in conformity to an Entity which is associated with it.

This page shows an example how to manage information which has complex data-structure in this system as an example of an information management system of a library. This system manages book location information (where book is arranged in), book management information (what kind book is registered) and lending information (which book is lent to whom). The following an E-R diagram that descfribes the data-model of this system.

<img src='/content/getting_started/airone_overview1.png' width='800'/>

You can easily manage those complex information by making Entities on Air One as below.

<img src='/content/getting_started/airone_overview2_entity.png' width='800'/>

And by making Entries, you can register and retrieve all kind of data instances which are mentioned above.

<img src='/content/getting_started/airone_overview3_entry.png' width='800'/>

In this way, user can handle any kind of information and information which is associated with other ones by using this simple data-structure (Entity and Entry) other than above use-case. For more information about this AirOne's datastructure, please see [Entity and Entry]() page.
