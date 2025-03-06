---
title: CustomView
weight: 0
---

# Custom View

## Overview

Custom Views in Pagoda allow developers to extend the standard UI with their own React-based interfaces. This feature enables you to create specialized views that leverage Pagoda's core functionality while providing tailored user experiences for specific use cases.

By using Custom Views, you can build interfaces that:
- Present data in specialized formats
- Implement domain-specific workflows
- Integrate with Pagoda's data model and ACL system
- Provide alternative navigation or interaction patterns

## What You Can Do with Custom Views

Custom Views enable you to:

- **Create specialized interfaces**: Build custom dashboards, data visualizations, or domain-specific tools
- **Integrate with Pagoda's core**: Access and manipulate data using Pagoda's data models and services
- **Implement custom logic**: Add business logic specific to your use case
- **Extend the UI**: Provide alternative ways to view and interact with your data

## Relationship with Pagoda Core

Custom Views are built as React applications that integrate with Pagoda through the `PagodaProvider` component. This provider gives your Custom View access to:

- Pagoda's data models (Entity-Attribute-Value pattern)
- Authentication and authorization
- Search capabilities
- Other core services

The Pagoda Core (`@dmm-com/pagoda-core`) is bundled as a library that your Custom View can import and use, allowing you to focus on building your specific interface rather than reimplementing core functionality. This package is hosted on GitHub Registry at [https://github.com/dmm-com/pagoda/pkgs/npm/pagoda-core](https://github.com/dmm-com/pagoda/pkgs/npm/pagoda-core).

> **Note**: Since `@dmm-com/pagoda-core` is hosted on GitHub Registry, you'll need to configure npm to access GitHub packages. Make sure you have appropriate GitHub access and authentication set up before installing the package.

## Getting Started with Custom View Development

### Prerequisites

- Node.js (v16 or later)
- npm (v7 or later)
- Basic knowledge of React and TypeScript
- GitHub access (for installing `@dmm-com/pagoda-core` from GitHub Registry)

### Step 1: Configure npm for GitHub Registry

Before installing dependencies, configure npm to access the GitHub Registry:

```bash
# Create or edit .npmrc in your project root
echo "@dmm-com:registry=https://npm.pkg.github.com" >> .npmrc

# Authenticate with GitHub (you'll need a personal access token with appropriate permissions)
npm login --registry=https://npm.pkg.github.com --scope=@dmm-com
```

### Step 2: Clone the Example Project

Start by cloning the example Custom View project:

```bash
git clone https://github.com/syucream/pagoda-customview-example
cd pagoda-customview-example
```

### Step 3: Install Dependencies

Install the required dependencies:

```bash
npm install
```

### Step 4: Run the Development Server

Start the development server:

```bash
npm run dev
```

This will:
- Start a local development server (typically at http://localhost:5173)
- Enable hot module replacement for quick development
- Watch for file changes and automatically rebuild

### Step 5: Understand the Project Structure

The example project demonstrates:
- How to use the `PagodaProvider` to integrate with Pagoda
- Basic project structure for a Custom View
- How to access Pagoda's core functionality

### Step 6: Build Your Custom View

When building your own Custom View:

1. Wrap your application with `PagodaProvider`
2. Use Pagoda's core services to access and manipulate data
3. Implement your custom UI components
4. Add any additional business logic specific to your use case

### Step 7: Build for Production

When ready to deploy:

```bash
npm run build
```

This will create a production-ready build of your Custom View that can be integrated with Pagoda.

## Development Notes

- The development server supports hot reloading - changes will be reflected immediately in the browser
- TypeScript errors will be shown in both the terminal and browser console
- The application integrates with Pagoda Core for base functionality

## Example Use Cases

- **Specialized Data Visualization**: Create custom charts or graphs for your data
- **Domain-Specific Workflows**: Implement guided workflows for specific business processes
- **Alternative Navigation**: Provide different ways to browse and search your data
- **Integration with External Systems**: Connect Pagoda data with other systems or APIs

By leveraging Custom Views, you can extend Pagoda's capabilities while maintaining the benefits of its core data management and ACL systems.
