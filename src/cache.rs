use crate::db::{list_origins, Origin};
use parking_lot::RwLock;
use sqlx::SqlitePool;
use std::collections::HashMap;
use std::sync::Arc;

use crate::error::AppError;

#[derive(Debug)]
pub struct OriginCache {
    origins: Arc<RwLock<HashMap<String, Origin>>>,
    pool: Arc<SqlitePool>,
}

impl OriginCache {
    pub fn new(pool: Arc<SqlitePool>) -> Self {
        OriginCache {
            origins: Arc::new(RwLock::new(HashMap::new())),
            pool,
        }
    }


    pub async fn refresh(&self) -> Result<(), AppError> {
        let new_origins = list_origins(&self.pool).await?;
        let mut map = HashMap::new();
        for origin in new_origins {
            map.insert(origin.domain.clone(), origin);
        }
        *self.origins.write() = map;
        Ok(())
    }

    pub async fn get(&self, domain: &str) -> Option<Origin> {
        tracing::info!("Get called on cache for domain: {}", domain);
        let origins = self.origins.read();
        let result = origins.get(domain).cloned();

        if result.is_some() {
            tracing::info!("Found origin in cache");
        } else {
            tracing::info!("Origin not found in cache");
        }
        result
    }
}
