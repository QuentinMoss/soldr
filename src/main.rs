use anyhow::Result;
use clap::Parser;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    #[arg(short, long)]
    config_path: Option<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "soldr=info".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    let args = Args::parse();
    let config = match args.config_path {
        Some(path) => read_config(&path)?,
        None => soldr::Config::default(),
    };

    let (ingest, mgmt, retry_queue) = soldr::app(config).await?;

    let addr = "0.0.0.0:3443";
    let addr = addr.parse()?;
    tokio::spawn(async move {
        tracing::info!("management API listening on {}", addr);
        axum::Server::bind(&addr)
            .serve(mgmt.into_make_service())
            .await
            .unwrap();
    });

    tokio::spawn(async move {
        tracing::info!("starting retry queue");
        retry_queue.start().await;
    });

    let addr = "0.0.0.0:3000";
    tracing::info!("ingest listening on {}", addr);
    axum::Server::bind(&addr.parse()?)
        .serve(ingest.into_make_service())
        .await?;

    Ok(())
}

fn read_config(config_path: &str) -> Result<soldr::Config> {
    let content = std::fs::read_to_string(config_path)?;
    Ok(toml::from_str(&content)?)
}
