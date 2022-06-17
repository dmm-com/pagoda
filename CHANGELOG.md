# Changelog

## In development

### Added

### Changed
* (New-UI) Added movable Atttribute button at editing Entity page
  Contributed by @hinashi, @syucream, @userlocalhost

### Fixed

## v3.10.0

### Added
* (New-UI) Implemented a new page that shows referral Entries
  Contributed by @syucream

### Fixed
* Fixed empty display of array type in advanced search result
  Contributed by @hinashi
* Fixed raising exception on validating URL
  Contributed by @syucream

## v3.9.0

### Changed
* Changed entity import to import entries belonging to multiple entities
  Contributed by @syucream

### Fixed
* Fixed model and UI problems that are related with Role
  Contributed by @userlocalhost
* Fixed an error when copying a lot of entries
  Contributed by @hinashi
* Fixed some model and UI problems related with new added Role feature
  Contributed by @userlocalhost
* Added URL validation processing when user specify webhook configuration
  for Entity
  Contributed by @syucream

## v3.8.0

### Changed
* Changed user model of django
  Contributed by @hinashi

## v3.7.0

### Added
* Added add and remove attributes depending on entity in get entry api v2
  Contributed by @hinashi
* Added custom processing when after delete entry
  Contributed by @hinashi
* Added new feature Role that has permissions which users (and groups)
  that are belonged to Role could access to information (#462)
  contributed by @userlocalhost
* Added create, update, delete, restore entry api in APIv2
  Contributed by @hinashi

### Changed
* Deny duplicated active entity attribute names
  Contributed by @syucream

### Fixed
* Fixed by validate length of entity/attr name
  Contributed by @syucream

## v3.6.0

### Changed
* Set entry-id for each entry columns in the list entry page
* Changed the logging method from airone profile to logging middleware
  Contributed by @hinashi
* Changed to separate settings for each environment by django-configrations
  Contributed by @hinashi

### Fixed
* Fixed problems that changing values for group won't be shown correctly
  in the changing entry's attribute page
* Fixed problem to return attribute information that has already been
  deleted (#400)
* Fixed exception error in /entry/do_edit/ (#443)
  Contributed by @hinashi
* Fixed problem that none of AttributeValue have is_latest is True (#441)
  Contributed by @hinashi
* Fixed that can be retrieved without permission in Entry API v2
  Contributed by @hinashi
* Fixed request even if the password is empty on change ldap auth (#465)
  Contributed by @hinashi

## v3.5.0

### Added
* Added to be able to insert custom javascript

### Changed
* Updated Django version that fixed security bug (CVE-2021-44420)
* Droped Python 3.6 support
* Upgrade celery version from v4.4.7 to v5.2.2
* Upgrade kombu version from v4.6.11 to v5.2.2
* Upgrade flower version from v0.9.7 to v1.0.0
* Upgrade django-filter version from v1.1.0 to v2.4.0

### Fixed
* Fixed an issue where advanced search narrow down was slow (#321)
* Fixed not being able to use regexp in entry names in the entry search API (#314)
* Fixed an exception error when specifying an invalid parameter in advanced search (#327)
* Fixed the order of entities when is_all_entities is specified in advanced search (#330)
* Fixed that cannot be retried after error when narrowing down in advanced search (#332)
* Fixed an issue with array type attributes when copying entries (#342)
* Fixed take a long time to create entry (#352)

### Refactored
* Refactored referral param in advanced search (#326)
* Refactored the process of check permission
* Refactored the process of get_available_attrs in Entry
* Refactored drf response format and default settings

## v3.4.1

## Fixed
* Fixed an error when specifying old parameters in advanced search (#323)
* Fixed different count of ret_values in advanced search results (#324)

## v3.4.0

### Added
* Added param of editting user for ldap (#256)
* Added attach referring entries on yaml export
* (WIP) Added a new UI in React

### Changed
* Changed redirect authenticated users to the top page
* Changed cookie of session to secure attribute, and to return HSTS header (#257)

### Fixed
* Fixed that the entry being created cannot be deleted (#242)
* Fixed update history of TOP page (#258)
* Fixed unused URL settings (#278)
* Fixed Escape \ on ES query
* Fixed a missing null check on the deleted list entry page
* Fixed an issue that caused redirects by incorrect URL links
* Fixed implementation for ACL inheritance for Attribute
* Fixed no permission check in advanced search and simple search(#282)
* Fixed a different number of entries displayed on the entity dashboard (#308)

### Refactored
* Refactored the entry list page

## v3.3.1

### Fixed
* Fixed bug AttributeValue.parent_attr is different with child's one (#272)

## v3.3.0

### Added
* Added the django-replicated library (#166)
* Added job function that cannot be canceled (#199)

### Changed
* Changed to remove complement_attrs when requesting show entry page (#166)
* Changed the logout from GET to POST (#166)
* Changed the HTTP method on the entry.export page from GET to POST (#166)
* Changed not to create tokens with GET user.access_token API (#166)
* Changed the behavior of token refresh (#208)
* Upgrade Django version from v3.2.4 to v3.2.5 (#254)

### Fixed
* Fixed the problem that the URL of Webhook API is different (#202)
* Fixed some attributes are not updated in advanced search results (#230)

## v3.2.0

### Changed
* Update Django to version 3.2.4 LTS (#153)

### Fixed
* Fixed the result being different depending on the hint_attr_value of
  search_entries (#158)
* Fixed a problem in the processing of import entry (#159)
* Fixed `urls` to avoid some warnings (#174)
* Fixed LDAP error output due to authentication failed (#179)
* Fixed a warning log with an SSL connection to the extarnal (#182)
* Fixed an exception error when specifying an invalid offset in GET entry API (#183)
* Fixed a bug that raises an exception at API handler of update entry (#186)

## v3.1.0

### Added
* Added `^` and `$` operators on filtering attribute values in advanced search
  result (#97). But there is a limitation that it could available only for
  'text' and 'string' typed attributes (see also #129).
* Added a new feature to be able to notify 3rd party systems through with
  calling webhook endpoints when Entry is created, edited and deleted.
  (NOTE: This requires to change DB schema. see also #135)
* Added a feature to be able to pagenate Entries in the list page for each
  Entities (#114).
* Added "django.contrib.humanize" to the INSTALLED_APPS to be able to handle
  data as a human touched one.
* Expanded Entry.to_dict to be able to more detail information.

### Changed
* Replace ldap3 with python-ldap for solving license problem (#134).
* Support Python 3.8
  * Update Celery and Kombu version
    * Celery from v4.2.0 to v4.4.7
    * Kombu  from v4.2.1 to v4.6.11

### Fixed
* Fixed a bug that entries which are searched in an editing page's form would
  not be found (#124).
* Fixed a search query timeout for long keywords (#145)
* Fixed a minor problem about version displaying

## v3.0.0

### Added
* Added handler to report celery exception errors
* Added password-reset feature
* Added perform client-side validation on users form

### Changed
* Update Django version from v1.11 to v2.2 (LTS)
* Droped Python 3.5 support

### Fixed
* Fixed not being redirected to the original URL after login
* Fixed some request logs not output
* Fixed the log message was not output to django.log
* Fixed the search form on the nav bar cannot handle whitespaces appropriately
* Fixed a bug at the background processing of creating Entry
* Fixed show error messages on create-user

## v2.7.0

### Changed
* Changed implementation of Entity to create, edit and delete it at Celery.
* Changed to show unauthorized entity on the dashboard

## v2.6.0

### Added
* Added param of entry refferal API to reduce filter execution time

### Changed
* Changing spec to show whole entity in the entity-list page regardless of thier permissions

### Refactored 
* Refactored the API handler for authentication to optimize DB query

## v2.5.1

### Fixed
* Fixed the Refer of EntityAttr failing to import
* Fixed the upper limit when using offset of GET entry API
* Fixed for API request without token results in exception error
* Fixed problems of profiler related with API request handlers

## v2.5.0

### Added
* Added docker-compose.yml

### Changed
* Changed custom_view before editing the entry

### Fixed
* Fixed for API request without token results in exception error
* Fixed "date" and "array_group" is not output in exporting CSV with advanced search
* Fixed a bug not to change referral values when entity was edited

## v2.4.0

### Changed
* Change implementation about editing Entity to disable to edit type of EntityAttr

## v2.3.1

### Fixed
* Fixed a problem that date value won't be shown at advanced search result

## v2.3.0

### Added
* Added new AttributeType `array group` that could contain multiple Group referral in an Attribute value

## v2.2.0

### Added
* Added a method in Entry to get an AttributeValue from Entry object with a small number of SQL

## v2.1.0

### Added
* Added an API endpoint that returns change history of specific entry's attribute.
* Added a feature to be able to confirm job of deleting entry from Job list view (#10)

## v2.0.1

### Fixed
* Fixed a bug that mandatory parameter was able to be updated with empty value by specifying '- NOT SET -' value (#20)

## v2.0.0

### Added
* Added a new optional authentication feature which is able to authenticate user with LDAP server (#6)
