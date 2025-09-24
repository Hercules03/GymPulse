/**
 * Extract all unique categories from branch data
 */
export function extractCategoriesFromBranches(branches: any[]): string[] {
  const categoriesSet = new Set<string>();

  branches.forEach(branch => {
    if (branch.categories) {
      Object.keys(branch.categories).forEach(category => {
        categoriesSet.add(category);
      });
    }
  });

  return Array.from(categoriesSet).sort();
}

/**
 * Extract categories from a single branch
 */
export function extractCategoriesFromBranch(branch: any): string[] {
  if (!branch.categories) return [];
  return Object.keys(branch.categories).sort();
}

/**
 * Get category display name with proper capitalization
 */
export function getCategoryDisplayName(category: string): string {
  return category.charAt(0).toUpperCase() + category.slice(1);
}

/**
 * Check if a category exists in the given branches
 */
export function isCategoryAvailable(category: string, branches: any[]): boolean {
  return branches.some(branch =>
    branch.categories && branch.categories[category]
  );
}