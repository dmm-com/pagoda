/* tslint:disable */
/* eslint-disable */
/**
 *
 * No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)
 *
 * The version of the OpenAPI document: 0.0.0
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { exists, mapValues } from "../runtime";
/**
 *
 * @export
 * @interface ACLParent
 */
export interface ACLParent {
  /**
   *
   * @type {number}
   * @memberof ACLParent
   */
  id?: number;
  /**
   *
   * @type {string}
   * @memberof ACLParent
   */
  name?: string;
  /**
   *
   * @type {boolean}
   * @memberof ACLParent
   */
  isPublic?: boolean;
}

/**
 * Check if a given object implements the ACLParent interface.
 */
export function instanceOfACLParent(value: object): boolean {
  let isInstance = true;

  return isInstance;
}

export function ACLParentFromJSON(json: any): ACLParent {
  return ACLParentFromJSONTyped(json, false);
}

export function ACLParentFromJSONTyped(
  json: any,
  ignoreDiscriminator: boolean
): ACLParent {
  if (json === undefined || json === null) {
    return json;
  }
  return {
    id: !exists(json, "id") ? undefined : json["id"],
    name: !exists(json, "name") ? undefined : json["name"],
    isPublic: !exists(json, "is_public") ? undefined : json["is_public"],
  };
}

export function ACLParentToJSON(value?: ACLParent | null): any {
  if (value === undefined) {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  return {
    id: value.id,
    name: value.name,
    is_public: value.isPublic,
  };
}