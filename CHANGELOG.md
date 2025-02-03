# Changelog

## In development

### Added

### Changed

### Fixed

## v3.119.0

### Changed
* Refactor AdvancedSearchAPI to improve type safety and code readability
  Contributed by @syucream

## v3.118.0

### Added
* Enable to get items considering with Alias name (by simple solution)
  Contributed by @userlocalhost

### Changed
* Optimize role import for job execution
  Contributed by @tsunoda-takahiro

### Fixed
* Fix filtering of inactive users and groups in RoleExportAPI
  Contributed by @tsunoda-takahiro

## v3.117.0

### Changed
* Added '@emotion/styled' as a peer dependency in package.json and updated webpack configuration to include it as an external dependency.
  Contributed by @syucream

## v3.116.0

### Fixed
* Fixed an error of auto-generate script by formality setting of DRF configuration.
  Contributed by @userlocalhost

## v3.115.0

### Added
* Introduced a new feature to identify Item using another names that are related with
  specific Item (it is named as Alias).
  Contributed by @hinashi, @userlocalhost
* Allow customviews to use/modify theme.
  Contributed by @syucream

## v3.114.0

### Fixed
* Fixed not being able to cancel a job from the Job menu.
  Contributed by @hinashi

## v3.113.0

### Fixed
* Fix Elasticsearch update on entry deletion.
  Contributed by @tsunoda-takahiro

## v3.112.0

### Fixed
* Fixed problem that might raise ElasticsearchException depends on context by
  SearchChain processing.
  Contributed by @hinashi, @userlocalhost

## v3.111.0

### Added
* Enable to pass general external parameters(`extendedGeneralParameters`) to React-UI
  implementation via Django template.
  Contributed by @userlocalhost, @hinashi

## v3.110.0

### Added
* Introduce isReadonly flag at the AdvancedSearchResult page.
  Contributed by @userlocalhost

### Changed
* Changed to not update ElasticSearch when editing entity.
  Contributed by @hinashi

## v3.109.0

### Changed
* Update duplicate entity name error handling.
  Contributed by @tsunoda-takahiro
* Update react-router from v5 to v6.
  Contributed by @syucream

## v3.108.0

### Changed
* Changed the order of before delete custom views.
  Contributed by @hinashi
* Changed to disabled 1pw for name-related attributes.
  Contributed by @syucream

## v3.107.0

### Added
* Allow to change header color to show environment deferences etc.
  Contributed by @syucream

## v3.106.0

### Changed
* small opmitization on entity/entry list API.
  Contributed by @syucream
* Update openapi-generator from v6.6.0 to v7.8.0
  Contributed by @syucream

## v3.105.0

### Fixed
* Reduce N+1 on join attrs.
  Contributed by @syucream

## v3.104.0

### Fixed
* Enable to import sjis encoded files.
  Contributed by @syucream

## v3.103.0

### Changed
* Change key of AdvancedSearchAttributeIndex for NAMED_* attributes from "name" parameter to referral Entry's name.
  Contributed by @userlocalhost, @hinashi

## v3.102.0

### Changed
* Separate loading stype between normal and join_attr.
  Contributed by @syucream
* Use datepicker in datetime type too.
  Contributed by @syucream

## v3.101.0

### Changed
* Wrap all the tasks with the decorators.
  Contributed by @syucream

### Fixed
* bugfix deleted objects are not displayed in role list page.
  Contributed by @tsunoda-takahiro

## v3.100.0

### Changed
* Simplify Entity - EntityAttr relation 1:N.
  Contributed by @syucream

## v3.99.0

### Changed
* Simplify Entry - Attribute relation 1:N.
  Contributed by @syucream

## v3.98.0

### Added
* Added helper class tmethod Entry.get_referred_entries() to get referral Entries from multiple referred Entries.
  Contributed by @userlocalhost
* Enable target_id filter on the job list API v2.
  Contributed by @syucream

### Changed
* Change エンティティ to モデル, エントリ to アイテム in newUI.
  Contributed by @userlocalhost

### Fixed
* Configured Elasticsearch to use a persistent data volume for index retention.
  Contributed by @tsunoda-takahiro
* Fix issue where re-added attribute's value appears in advanced search.
  Contributed by @tsunoda-takahiro

## v3.97.0

### Added
* Added processing to check whether user agrees with the Terms of Service when
  settings.AIRONE["CHECK_TERM_SERVICE"] is activated.
  Contributed by @userlocalhost, @hinashi
* Added new middleware to prevent to exposing old URL when
  LEGACY_UI_DISABLED parameter is set in the settings.AIRONE
  Contributed by @userlocalhost

### Fixed
* Fixed failed invoke trigger for oldUI.
  Contributed by @hinashi

## v3.96.0

## Added
* Added tooltip for long entry name.
  Contributed by @hinashi
* Added safety processing to prevent changing user password when PASSWORD_RESET_DISABLED is set.
  Contributed by @userlocalhost

### Fixed
* Fixed some N+1 query.
  Contributed by @syucream

## v3.95.0

### Fixed
* Fixed some N+1 query.
  Contributed by @syucream

## v3.94.0

## Changed
* Migrate to enum based ACLType.
  Contributed by @syucream

## v3.93.0

### Added
* Support datetime attribute type.
  Contributed by @syucream

### Changed
* Enhanced date validation to support both YYYY-MM-DD and YYYY/MM/DD formats.
  Contributed by @tsunoda-takahiro

## v3.92.0

### Changed
* Added an option to be able to disable showing history page of Item from entry details page
  Contributed by @userlocalhost
* Changed the location of custom view library.
  Contributed by @hinashi

## v3.91.0

### Changed
* Removed Basic Auth support.
  Contributed by @hinashi

## v3.90.0

### Changed
* Updated to delete obsoleted title to new one, which is defined in the Django configuration file.
  Contributed by @hinashi, @userlocalhost
* Migrate to enum based AttrType.
  Contributed by @syucream

## v3.89.0

### Changed
* Upgrade django version from 3.2.25 to 4.2.11
  Contributed by @syucream
* Disable to show change password feature when PASSWORD_RESET_DISABLED environment variable is set.
  Contributed by @hinashi, @userlocalhost

### Fixed
* Fixed bug not to be able to login because of CSRF token failure at the login page.
* Prevent to showing both adding user and importing user/group pages by ordinary user.
  Contributed by @userlocalhost, @hinashi

## v3.88.0

### Added
* Added pydantic model in export v2.
  Contributed by @syucream

## v3.87.0

### Added
* Added test in parallel.
  Contributed by @syucream

* Show 'ongoing' status on entity if it has non-finished jobs.
  Contributed by @syucream

### Changed
* Enable to get search advanced_search results sequentially and check its progres
  when join_attr parameter is specified.
  Contributed by @userlocalhost, @hinashi

## v3.86.0

### Added
* Added advanced search chain apiv2.
  Contributed by @hinashi

### Changed
* Refactor entry exports.
  Contributed by @syucream

## v3.85.0

### Changed
* Update background processing to support any OBJECT typed Attribute for join_attr
  at the advacend serarch processing.
  Contributed by @userlocalhost
* Simplify some remaining entry tasks additionally.
  Contributed by @syucream

### Fixed
* Fixed an error when specifying all entities in advanced search.
  Contributed by @hinashi
* Fixed a problem not to be able to invoke Trigger when an Item is not updated,
  but it sould be invoked trigger for applying setting default value trigger.
  Contributed by @hinashi, @userlocalhost

## v3.84.0

### Added
* Added Attribute type (`named_object` and `array_named_object`) for TriggerAction
  Contributed by @userlocalhost, @hinashi
* Added env to add middleware settings.
  Contributed by @hinashi

### Changed
* Refactored to use IntEnum.
  Contributed by @syucream

## v3.83.0

### Added
* Added new feature that user can get referred Item's contents that an Item
  of advanced search result refers to from advanced search result page.
  Contributed by @userlocalhost, @hinashi

### Changed
* Upgrade DRF version from v3.11.2 to v3.15.1
  Contributed by @syucream

## v3.82.0

### Added
* Enable to check verification error details on webhooks by users.
  Contributed by @syucream

### Changed
* Use enum on the job status.
  Contributed by @syucream

## v3.81.0

### Changed
* Support celery task for entry APIv2.
  Contributed by @syucream

## v3.80.0

### Changed
* Add privileged mode at DRF serializer of Entry mainly for custom_view processing
  Contributed by @userlocalhost
* Improve job class with type hints and enum
  Contributed by @syucream

## v3.79.0

### Fixed
* Fix description for isTopLevel.
  Contributed by @syucream

## v3.78.0

### Changed
* Renamed frontend page component.
  Contributed by @syucream

### Fixed
* Fixed invoke trigger failure with do_edit.
  Contributed by @hinashi

## v3.77.0

### Changed
* Enable to invoke TriggerAction when import and revert processing.
  Contributed by @hinashi, @userlocalhost

### Fixed
* Fix deps to avoid inifinite fetching in acl history page.
  Contributed by @syucream

## v3.76.0

### Changed
* Upgrade django version from 3.2.23 to 3.2.24

## v3.75.0

### Added
* Added new feature TriggerAction to be able to update Attributes along with user defined configuration.
  Contributed by @userlocalhsot, @hinashi
* Enable collecting coverage on the frontend.
  Contributed by @syucream

### Changed

### Fixed
* Fix download links shown in header menu.
  Contributed by @syucream

## v3.74.0

### Added
* Changed so that SSO login is also redirected to the next URL.
  Contributed by @hinashi

## v3.73.0

### Added
* Allow the error page to reload.
  Contributed by @syucream
* Notify copying access token via snackbar.
  Contributed by @syucream
* Support changing auth method (local -> LDAP).
  Contributed by @syucream

### Fixed
* Fixed an issue where array type attributes added later were not registered in ES
  Contributed by @hinashi

## v3.72.0

### Changed
* Migrate CircleCI to GitHub Actions.
  Contributed by @syucream
* Enable to toggle webhook feature.
  Contributed by @syucream

## v3.71.0

### Fixed
* Fixed advanced search when referral is deleted in array_named_entry type.
  Contributed by @hinashi
* Fixed slow ACL search and update.
  Contributed by @hinashi

## v3.70.0

### Changed
* Change specification of Entry.get_available_attrs() for deleted referral for UX.
  Contributed by @userlocalhost

## v3.69.0

### Added
* Support basic i18n support.
  Contributed by @syucream

### Fixed
* Reset ErrorBoundary on relocations.
  Contributed by @syucream

## v3.68.0

### Fixed
* Fixed an exception error when updating to too long entry name.
  Contributed by @tsuneyama-tomo, @cui-songhe
* Fixed bug that raise exception when '&' was specified.
  Contributed by @tsuneyama-tomo, @cui-songhe

## v3.67.0

### Added
* Add date/boolean type specific attr filter selector.
  Contributed by @syucream
* Enable to optout the path to legacy UI on the new UI.
  Contributed by @syucream

### Changed
* Changed environmental variable type of EXTENDED_HEADER_MENUS that accpet from user.
  Contributed by @userlocalhost, @hinashi

## v3.66.0

### Added
* Enable to limit the number of records.
  Contributed by @syucream
* Added job download APIv2 that allows you to specify the format.
  Contributed by @hinashi

### Changed
* Allow to submit if any fields are dirty in edit pages.
  Contributed by @syucream

## v3.65.0

### Fixed
* Avoid unnecessary re-loading on entity selector.
  Contributed by @syucream
* Fixed unnecessary re-rendering in advanced search params.
  Contributed by @syucream

## v3.64.0

### Added
* Added limit for frequent import jobs on the same entity.
  Contributed by @syucream
* Add sso login link on the new login page.
  Contributed by @syucream
* Show loading icon in submit button during submitting to the backend.
  Contributed by @syucream
* Refresh recent jobs on click job menu.
  Contributed by @syucream

## v3.63.0

### Added
* Add DataUtil.formatDate() that only returns date (without time) string value from Date instance.
  Contributed by @userlocalhost

### Changed
* Reimplement advanced search result export v2.
  Contributed by @syucream

### Fixed
* Fixed required for mandatory attributes when renaming using entry update API.
  Contributed by @hinashi
* Fixed exception error in entry import.
  Contributed by @hinashi

## v3.62.0

### Added
* Show login user name on the header.
  Contributed by @syucream

### Changed
* Support Python 3.11
  Contributed by @syucream

## v3.61.0

### Added
* Add note field to EntityAttr.
  Contributed by @syucream

### Changed
* Changed to use poetry.
  Contributed by @syucream

### Fixed
* Fixed do not crash if refreshing jobs failed.
  Contributed by @syucream

## v3.60.0

### Changed
* Changed OpenAPI generator result to NPM package.
  Contributed by @syucream
* Refactored advanced search pagination.
  Contributed by @syucream
* Redactored get group info in edit role page.
  Contributed by @yoshi-non
* Improved behavior when clearing advanced search result filtering.
  Contributed by @Bayathy
* Changed tabs to prohibited characters in entry names.
  Contributed by @Limitex

### Fixed
* Fixed numeric update in entry API.
  Contributed by @nameless-mc
* Fixed bug of EntryList menu to show deleted Entry just after deleting.
  Contributed by @sniper-fly
* Fixed AdvancedSearchModal to keep filterKey info after resetting attributes.
  Contributed by @sniper-fly

## v3.59.0

### Changed
* Changed value type for named_entry attribute.
  Contributed by @hinashi

## v3.58.0

### Changed
* Enable to import objects have same name safely.
  Contributed by @syucream
* Bumping up pyyaml version for fixing npm packaging failure.

### Fixed
* Fixed a bug not to be able to get AttributeValue instance when
  an EntityAttr's name was changed after creating Entry.
  Contributed by @userlocalhost, @hinashi
* Fix entry copy and entry list pages.
  Contributed by @syucream

## v3.57.0

### Changed
* Convert to Blob before calling APIV2 client method.
  Contributed by @syucream

### Fixed
* Fixed problem that prohibited attribute to be edited is set to blank at Entry edit processing (#899).
  Contributed by @userlocalhost, @hinashi
* Fixed acl history page.
  Contributed by @hinashi

## v3.56.0

### Changed
* Use path based import to reduce bundle size.
  Contributed by @syucream

### Fixed
* Fixed acl setting page.
  Contributed by @hinashi

## v3.55.0

### Added
* Support bulk delete entries.
  Contributed by @syucream

### Fixed
* Fixed entry histoty page.
  Contributed by @hinashi

## v3.54.0

### Added
* Support text not contained filter key in advanced search.
  Contributed by @syucream

### Fixed
* Fixed restore entry page.
  Contributed by @hinashi

## v3.53.0

### Added
* Enabled to search Entries that has same AttributeValue at the advanced search processing.
  Contributed by @hinashi, @userlocalhost, @syucream

### Changed
* Upgrade django version from 3.2.19 to 3.2.20
* Represent authenticate_type as an enum value.
  @syucream
* Disallow blank entry name on the new UI.
  @syucream

## v3.52.0

### Added
* Added ACL history page.
  Contributed by @syucream
* Added helm chart.
  Contributed by @hinashi

## v3.51.0

### Changed
* Refactoring joblist.
  Contributed by @syucream
* Refactored entry edit page.
  Contributed by @hinashi

## v3.50.0

### Changed
* Create repository layer and reorganize service layer.
  Contributed by @syucream

### Fixed
* Fixed deleting entries in entry edit.
  Contributed by @hinashi

## v3.49.0

### Added
* Prepare to publish APIv2 client npm package w/o modifying existing code.
  Contributed by @syucream

### Changed
* Upgrade django version from 3.2.18 to 3.2.19
* Hide disallowed value explicitly on advanced search result.
  Contributed by @syucream

### Fixed
* Fixed error when date attribute value is None in advanced search.
  Contributed by @hinashi

## v3.48.0

### Changed
* Implement isMandatory value validation.
  Contributed by @syucream
* Hide entry attribute if user isn't allowed to show it
  Contributed by @syucream

### Fixed
* Fixed a bug of /api_v1/entry/search_chain API implementation at the "refers" condition.
  This unables to filter intermediate search results with Entry name at its condition.
  Contributed by @userlocalhost
* Fixed the order of attributes in the entry edit to index order.
  Contributed by @hinashi
* Fixed edit entries when special characters are used in attribute names.
  Contributed by @hinashi
* Fixed celery trace log not output
  Contributed by @hinashi

## v3.47.0

### Added
* Added django-storages library.
  Contributed by @hinashi

### Changed
* Upgrade TypeScript version to 5.x.
  Contributed by @syucream
* Validate input entry data with Zod.
  Contributed by @syucream
* Changed the entry form to be customizable with custom views.
  Contributed by @hinashi, @syucream, @userlocalhost

## v3.46.0

### Fixed
* Fixed a bug to be able to edit Entry, Attribute and EntityAttr's ACL without Full permission
  Contributed by @userlocalhost

## v3.45.0

### Added
* Added django-environ library.
  Contributed by @hinashi

### Changed
* Validate input entity data with Zod.
  Contributed by @syucream

## v3.44.0

### Changed
* Validate input acl data with Zod.
  Contributed by @hinashi, @syucream, @userlocalhost

### Fixed
* Fixed search chain API referral filtering.
  Contributed by @hinashi

## v3.43.0

### Changed
* Validate input user data with Zod.
  Contributed by @syucream
* Changed to increase the maximum value of SearchChainAPI.
  Contributed by @hinashi

### Fixed
* Fixed search chain API when only one filtering hit.
  Contributed by @hinashi

## v3.42.0

### Changed
* Validate input role data with Zod.
  Contributed by @syucream
* Replace sx props with styled components.
  Contributed by @syucream
* Upgrade django version from 3.2.17 to 3.2.18

### Fixed
* Fixed pagination error in entry history apiv2.
  Contributed by @hinashi

## v3.41.0

### Added
* Added to use Elasticsearch security features.
  Contributed by @hinashi
* Added customview in delete entry api.
  Contributed by @hinashi

### Changed
* Enable TypeScript strict mode.
  Contributed by @syucream

### Fixed
* Fixed permissions for entry operations.
  Contributed by @hinashi
* Fixed filter only ancestors and others not to break group tree
  Contributed by @syucream

## v3.40.0

### Changed
* Upgrade django version from 3.2.16 to 3.2.17
* Optimize role form with React Hook Form
  Contributed by @syucream

### Fixed
* Fixed the following bugs
  Contributed by @hinashi, @syucream, @userlocalhost
  - Fixed pagination count in list page
  - Fixed to add the first attribute into entity
  - Fixed edit entry when nothing role value
  - Fixed a bug not to be able to move correct page after creating Entity
  - Fixed append list value in edit array named entry
  - Fixed a bug not to be able to erase selected referral information at EntryEdit page
  
## v3.39.0

### Added
* Added feature to be able to sort Entries by created time order at list page
  Contributed by @userlocalhost

### Changed
* The first prototype of decoupling frontend implementation from
  presentation to service layer that only has JavaScript processing
  for increasing maintenancability.
  Contributed by @hinashi, @syucream, @userlocalhost
* Changed to use DjangoContext instead of login page static descriptions
  Contributed by @userlocalhost

### Fixed
* Fixed anchor link in edit entry.
  Contributed by @hinashi

## v3.38.0

### Added
* Added processing to be able to configure sort-order at list Entry page.
  Contributed by @userlocalhost
* Show entity link/name on job list
  Contributed by @syucream

### Changed
* Changed margins on all pages.
  Contributed by @hinashi

## v3.37.0

### Added
* Added django-simple-history library
  Contributed by @syucream, @userlocalhost, @hinashi

### Fixed
* Fixed wrong ACL criterion for copy and delete processing.
  Contributed by @userlocalhost

## v3.36.0

### Changed
* Changed model for Permission to be able to track history of each of them
  when Role permissions were changed
  Contributed by @syucream, @userlocalhost, @hinashi

## v3.35.0

### Added
* Added following features
  - Added attribute 'permissions' at export role feature.
  - Enable to receive data that has permissions attribute from import file.
  Contributed by @syucream, @userlocalhost, @hinashi
* Make app title a link to top page
  Contributed by @syucream
* Add a link to entry details page
  Contributed by @syucream
* Enable to simple-search on AppBar
  Contributed by @syucream
* Support pagination on advanced search result
  Contributed by @syucream
* Autofocus at simple search box on dashboard page
  Contributed by @syucream
* Enable to multi-select advanced search conditions from auto-completed items
  Contributed by @syucream
* Show entity name on simple search result
  Contributed by @syucream

### Changed
* Make attribute name field shorter
  Contributed by @syucream
* Replace with an empty element on deleting the first element on array-string and array-named-entry
  Contributed by @syucream

### Fixed
* Fixed a bug of Entry.search_entries() when None is passed at the user parameter.
  Contributed by @userlocalhost
* Fixed a bug not to be able to import Role just after exporting.
  Contributed by @hinashi, @userlocalhost
* Fixed exact match search results were excluded in simple search
  Contributed by @hinashi
* Don't show prompt when just showing edit user page
  Contributed by @syucream

## v3.34.0

### Changed
* Changed refresh recent job list periodically.
  Contributed by @syucream

## v3.33.0

### Changed
* Upgrade node version from 7.2 to 8.12
  Contributed by @hinashi

## v3.32.0

### Added
* Added new UI entity history.
  Contributed by @syucream
* Added new UI entry history.
  Contributed by @syucream

### Changed
* Changed str type and text type to not date format.
  Contributed by @hinashi

### Fixed
* Fixed not outputting in YAML export when there is no value in str, text type.
  Contributed by @hinashi
* Fixed an issue where role, array_role, boolean type was not output correctly in YAML export.
  Contributed by @hinashi

## v3.31.0

### Added
* Added new UI entity export and import.
  Contributed by @syucream

### Fixed
* Fixed problem not to be able to get boolean typed data with correct type
  Contributed by @hinashi, @userlocalhost

## v3.30.0

### Changed
* Refactored create/edit user page, along with amended design.
  Contributed by @hinashi, @userlocalhost

## v3.29.0

### Added
* Added new UI password reset page
  Contributed by @syucream

### Changed
* Upgrade Elasticsearch version from 6.8.16 to 7.17.6
  Contributed by @hinashi

## v3.28.0

### Added
* Added API v2 for User, Group, Role
  Contributed by @syucream
* Added new UI error page
  Contributed by @syucream

### Fixed
* Fixed the problem that ES registration process takes time
  Contributed by @hinashi

## v3.27.0

### Added
* Added API handler that searchs Entries across multiple referral structure
  (/api/v1/search_chain)
  Contributed by @userlocalhost, @hinashi
* Added group edit page.
  Contributed by @syucream

### Changed
* Improved processing to get referred Entry from elasticsearch
  (reducing number of DB access)
  Contributed by @userlocalhost, @hinashi
* Upgrade django version from 3.2.15 to 3.2.16

## v3.26.0

### Added
* Added group list page.
  Contributed by @syucream

### Fixed
* Fixed an issue where complement_attrs() called duplicates.
  Contributed by @userlocalhost

## v3.25.0

### Added
* Added a new API handler that user can retrieve Entries, which refers an Entry
  at specific Attribute and that referred Entry refers another Entry. In that way,
  user can specify this repeated (chained) reference condition to get Entry
  that refers far away Entry without aware of intermediate ones.
  Contributed by @userlocalhost
* Added role list and role edit page.
  Contributed by @syucream

### Changed
* Changed Elasticsearch update process to faster.
  Contributed by @hinashi
* Upgrade Elasticsearch version from 6.8.16 to 7.17.6
  Contributed by @hinashi

### Fixed
* Fixed advanced search not output after entity edit.
  Contributed by @hinashi

## v3.24.0

### Changed
* Changed not to execute notify job when there is no update in entry import
  Contributed by @hinashi

### Fixed
* Fixed error in updating array_object attribute
  Contributed by @hinashi
* Fixed remove_from_attrv for array_named_entry attribute
  Contributed by @hinashi

## v3.23.0

### Changed
* Changed not to use memcached.
  Contributed by @hinashi

## v3.22.0

### Added
* Added airone error code to APIv2 for frontend.
  Contributed by @syucream, @userlocalhost, @hinashi
* Added new parameter "as_member" at the Role.is_belonged_to() method to be able to
  confirm that specified user is belonged to this role as member.
  Contributed by @userlocalhost

## v3.21.0

### Added
* Added new Attribute-types ("role" and "array_role") that
  could refer Role instance from AttributeValue.
  Contributed by @userlocalhost

### Changed
* Upgrade flower version from 1.1.0 to 1.2.0

### Fixed
* Fixed Elasticsearch not updating when updating Group and Role.
  Contributed by @Ravie403
* Fixed showing deleted attributes in entry restore.
  Contributed by @Ravie403
* Fixed value not being displayed due to javascript error in entry edit.
  Contributed by @ritsuxis
* Fixed duplicate entries in entry restore.
  Contributed by @ritsuxis
* Fixed a problem that an exception will be occurred at edit Entry page.
  Contributed by @ritsuxis
* Fixed entity's page paginate.
  Contributed by @ritsuxis

## v3.20.0

### Added
* Added entity name at dashboard search result page.
  Contributed by @Ravie403

### Fixed
* Escaped single quote data will be shown at Entry edit page (#603)
  Contributed by @Ravie403
* Fixed value being displayed as null at advanced search results page.
  Contributed by @Ravie403
* Fixed referral entries not displayed at restore entry page.
  Contributed by @Ravie403
* Fixed value being displayed as null at restore entry page.
  Contributed by @Ravie403
* Fixed an error when there is no named_entry attribute value in advanced search.
  Contributed by @Ravie403

## v3.19.0

### Added
* Added special search character to get Entries
  that have substantial attribute values.
  Contributed by @userlocalhost

### Fixed
* Fixed problem that duplicate named Entries might be created
  when multiple requests were coming at the exact same time.
  Contributed by @userlocalhost, @hinashi

## v3.18.0

### Added
* (New-UI) Implemented ACL configuration page for Entity, Entry
  and EntityAttr.
  Contributed by @hinashi, @syucream, @userlocalhost
* Added exclude entity parameter in search_entries_for_simple.
  Contributed by @hinashi
* Added exclude entity parameter in get_referred_objects.
  Contributed by @hinashi

### Fixed
* Fixed an error in getting data_value in advanced search.
  Contributed by @hinashi

## v3.17.0

### Changed
* Changed to allow parallel execution some job.
  Contributed by @hinashi
* Changed to update job status to error when celery exception error
  Contributed by @hinashi

## v3.16.0

### Changed
* Introduced new Job's status WARNING, that is intermediate
  status between succeed and error.
  Contributed by @userlocalhost

## v3.15.0

### Fixed
* Fixed custom_view not applied when importing multiple entities
  Contributed by @hinashi

## v3.14.0

### Changed
* (New-UI) Show a shorten name if entity name is too long
  at Entity list view.
  Contributed by @syucream

### Fixed
* (New-UI) Perform animation when reordering entity attribute
  to highlight moved attribute on the form.
  Contributed by @syucream
* (New-UI) Fix bugs that failed to delete unsubmitted attribute.
  Contributed by @syucream
* (New-UI) Fix not to occur a warning on entity referral auto
  complete field.
  Contributed by @syucream

## v3.13.0

### Added
* (New-UI) Implemented creating/editing an Entry page that comply with
  new design.
  Contributed by @hinashi, @syucream, @userlocalhost

### Changed
* Upgrade django version from 3.2.13 to 3.2.14

## v3.12.0

### Added
* Added a new feature for Group, that can represent parent Group.
  This feature enables to make hierarchical tree Group construction.
  Contributed by @userlocalhost

### Changed
* Upgrade flower version from v1.0.0 to v1.1.0

### Fixed
* Fixed empty display of array type in advanced search result
  Contributed by @hinashi
* Fixed an issue where None was displayed in array_named_entry attribute
  Contributed by @hinashi
* Fixed the header of webhook is not set
  Contributed by @hinashi
* Fixed entry recovery and attribute value revert not sending webhooks
  Contributed by @hinashi

## v3.11.0

### Changed
* (New-UI) Added movable Atttribute button at editing Entity page
  Contributed by @hinashi, @syucream, @userlocalhost

## v3.10.0

### Added
* (New-UI) Implemented a new page that shows referral Entries
  Contributed by @syucream

### Fixed
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
