import React from "react";

export type ProductItem = {
  id: string;
  name: string;
  category: string;
  price: string;
  imageUri?: string;
};

type ProductListItemProps = {
	item: ProductItem;
	onEdit: () => void;
	onDelete: () => void;
};

export default function ProductListItem({ item, onEdit, onDelete }: ProductListItemProps) {
	return (
		<div className="group bg-gradient-to-r from-white to-primary/5 border border-border rounded-2xl p-4 mb-4 shadow-md hover:shadow-xl hover:shadow-primary/10 transition-all duration-300 hover:-translate-y-1">
			<div className="flex items-center gap-4">
				{/* Product Image */}
				<div className="relative flex-shrink-0">
					{item.imageUri ? (
						<img 
							src={item.imageUri} 
							alt={item.name} 
							className="w-16 h-16 object-cover rounded-2xl border-2 border-border group-hover:border-primary/30 transition-colors duration-300" 
						/>
					) : (
						<div className="w-16 h-16 bg-gradient-to-br from-primary/20 to-primary/10 rounded-2xl flex items-center justify-center border-2 border-border group-hover:border-primary/30 transition-colors duration-300">
							<span className="text-2xl">📦</span>
						</div>
					)}
				</div>

				{/* Product Info */}
				<div className="flex-1 min-w-0">
					<h3 className="text-lg font-bold text-text group-hover:text-primary transition-colors duration-300 truncate">
						{item.name}
					</h3>
					<p className="text-sm text-lightText mb-1 flex items-center gap-1">
						<svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
						</svg>
						{item.category}
					</p>
					<div className="text-xl font-bold text-primary">
						{item.price}
					</div>
				</div>

				{/* Action Buttons */}
				<div className="flex gap-2 items-center">
					<button 
						onClick={onEdit}
						className="w-10 h-10 bg-primary/10 hover:bg-primary/20 text-primary rounded-xl transition-all duration-300 hover:scale-110 active:scale-95 flex items-center justify-center group/btn"
						title="Editar producto"
					>
						<svg className="w-5 h-5 group-hover/btn:scale-110 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
						</svg>
					</button>
					<button 
						onClick={onDelete}
						className="w-10 h-10 bg-red-50 hover:bg-red-100 text-red-600 rounded-xl transition-all duration-300 hover:scale-110 active:scale-95 flex items-center justify-center group/btn"
						title="Eliminar producto"
					>
						<svg className="w-5 h-5 group-hover/btn:scale-110 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
						</svg>
					</button>
				</div>
			</div>
		</div>
	);
}


