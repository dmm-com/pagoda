# Changelog

## In development

### Changed
* Update Django to version 3.2.4 LTS (#153)
* Changed to complement_attrs when adding the attribute of the entity (#166)

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
